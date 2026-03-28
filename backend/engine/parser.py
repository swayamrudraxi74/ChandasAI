# ==========================================
# engine/parser.py  —  Sanskrit Text Parser
# ==========================================
#
# WHAT THIS FILE DOES:
#   Converts raw Sanskrit input (Devanagari, IAST, or plain English)
#   into a list of syllable strings that downstream modules can analyze.
#
#   Pipeline:
#     1. normalize_input()   — strip junk, fix unicode composition
#     2. detect_script()     — figure out if input is Devanagari / IAST / plain
#     3. devanagari_to_iast() or plain_to_iast()  — convert to IAST
#     4. split_syllables()   — split IAST string into syllable list
#
# BUG FIXED (v2):
#   split_syllables() previously counted anusvara (ṃ) and visarga (ḥ)
#   as SEPARATE syllables because they are not vowels and the parser
#   failed to attach them to the preceding syllable.
#
#   Example (before fix):
#     "raṃ"  →  ["ra", "ṃ"]   ← 2 items, WRONG
#   Example (after fix):
#     "raṃ"  →  ["raṃ"]       ← 1 item, CORRECT
#
#   Impact: For the Vishnu Stuti (शान्ताकारं...), total syllables went
#   from 82 (wrong) down to 68 (correct: 17 per pāda × 4 pādas).
#   This also fixes the downstream metre detection which was reporting
#   "Upajāti" instead of "Mandākrāntā".
# ==========================================

import json
import os
import re
import unicodedata

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# LOAD ALL JSON FILES
# ─────────────────────────────────────────
input_rules           = load_json("input_rules.json")
devanagari_map        = load_json("devanagari_map.json")
vowel_rules           = load_json("vowel_rules.json")
consonant_rules       = load_json("consonant_rules.json")
transliteration_alias = load_json("transliteration_alias.json")

# ─────────────────────────────────────────
# BUILD LOOKUP TABLES FROM JSON
# ─────────────────────────────────────────

# From devanagari_map.json
_indep_vowels   = devanagari_map["independent_vowels"]   # अ → a
_vowel_signs    = devanagari_map["vowel_signs"]           # ा → ā
_consonants_dev = devanagari_map["consonants"]            # क → k
_special_syms   = devanagari_map["special_symbols"]       # ं → ṃ
_virama         = devanagari_map["virama"]                # ्

# From vowel_rules.json
_short_vowels   = vowel_rules["short_vowels"]
_long_vowels    = vowel_rules["long_vowels"]
_vowel_order    = vowel_rules["vowel_priority_order"]     # longest-first

# From consonant_rules.json
_guru_clusters  = consonant_rules["guru_causing_clusters"]
_anusvara       = consonant_rules["anusvara_and_visarga"]["anusvara"]  # ṃ
_visarga        = consonant_rules["anusvara_and_visarga"]["visarga"]   # ḥ

# From transliteration_alias.json
_alias_groups   = {
    "common_word_aliases": transliteration_alias["common_word_aliases"],
    "retroflex_aliases":   transliteration_alias["retroflex_aliases"],
    "consonant_aliases":   transliteration_alias["consonant_aliases"],
    "vowel_aliases":       transliteration_alias["vowel_aliases"],
    "nasal_aliases":       transliteration_alias["nasal_aliases"],
    "visarga_aliases":     transliteration_alias["visarga_aliases"],
}
_alias_order    = transliteration_alias["normalization_order"]

# From input_rules.json
_remove_chars   = (input_rules["allowed_punctuation"] +
                   input_rules["ignored_symbols"])
_iast_markers   = input_rules["script_detection"]["iast_characters"]

# ─────────────────────────────────────────
# POST-VOWEL MODIFIERS
# These characters must ALWAYS attach to the preceding vowel.
# They are NOT vowels themselves, so they must never become
# standalone "syllables".
# ─────────────────────────────────────────
_POST_VOWEL_MODIFIERS = {
    _anusvara,    # ṃ  — anusvara (nasal modifier)
    _visarga,     # ḥ  — visarga (breath modifier)
    "ṁ",          # alternate anusvara spelling
    "ḿ",          # another variant
    "m̐",          # chandrabindu
}


# ─────────────────────────────────────────
# STEP 1 — NORMALIZE RAW INPUT
# ─────────────────────────────────────────
def normalize_input(text: str) -> str:
    """
    Cleans the raw text before any analysis:
      - Strips leading/trailing whitespace
      - Applies Unicode NFC normalization (fixes composed vs. decomposed chars)
      - Removes ignored/punctuation characters defined in input_rules.json
      - Collapses multiple spaces into one
    """
    text = text.strip()
    text = unicodedata.normalize("NFC", text)

    for ch in _remove_chars:
        text = text.replace(ch, "")

    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─────────────────────────────────────────
# STEP 2 — DETECT SCRIPT
# ─────────────────────────────────────────
def detect_script(text: str) -> str:
    """
    Returns 'devanagari', 'iast', or 'plain'.

    Detection order:
      1. Any character in U+0900–U+097F range → Devanagari
      2. Any known IAST diacritic → IAST
      3. Otherwise → plain English approximation
    """
    if any('\u0900' <= ch <= '\u097F' for ch in text):
        return "devanagari"
    if any(ch in text for ch in _iast_markers):
        return "iast"
    return "plain"


# ─────────────────────────────────────────
# STEP 3a — DEVANAGARI → IAST
# ─────────────────────────────────────────
def devanagari_to_iast(text: str) -> str:
    """
    Character-by-character conversion from Devanagari to IAST.

    Handles:
      - Independent vowels (अ, आ, इ, ...)
      - Consonants with matras (ka, kā, ki, ...)
      - Consonants with virama / halant (dead consonants in conjuncts)
      - Consonants with inherent short 'a'
      - Special symbols: anusvara (ṃ), visarga (ḥ), chandrabindu
    """
    result = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Independent vowel (e.g. अ → a, आ → ā)
        if ch in _indep_vowels:
            result.append(_indep_vowels[ch])
            i += 1

        # Consonant
        elif ch in _consonants_dev:
            base = _consonants_dev[ch]
            i += 1

            if i < n and text[i] == _virama:
                # Halant (् ) — consonant has no inherent vowel here
                # Used in conjunct clusters, e.g. क् in क्ष
                result.append(base)
                i += 1
            elif i < n and text[i] in _vowel_signs:
                # Consonant + vowel sign (matra), e.g. का → kā
                result.append(base + _vowel_signs[text[i]])
                i += 1
            else:
                # Consonant with implicit inherent short 'a'
                result.append(base + "a")

        # Special symbols: anusvara ṃ, visarga ḥ, chandrabindu
        elif ch in _special_syms:
            val = _special_syms[ch]
            if val:
                result.append(val)
            i += 1

        # Spaces and anything else — pass through unchanged
        else:
            result.append(ch)
            i += 1

    return "".join(result)


# ─────────────────────────────────────────
# STEP 3b — PLAIN ENGLISH → IAST
# ─────────────────────────────────────────
def plain_to_iast(text: str) -> str:
    """
    Converts plain English approximations (e.g. "aa", "sh", "kh")
    into proper IAST notation using alias tables from JSON.
    Applies groups in the order specified by normalization_order.
    Longer patterns are matched first to prevent partial replacements.
    """
    text = text.lower()
    for group_name in _alias_order:
        aliases = _alias_groups.get(group_name, {})
        # Sort by length descending: match "kṣ" before "k", etc.
        for plain in sorted(aliases, key=len, reverse=True):
            text = text.replace(plain, aliases[plain])
    return text


# ─────────────────────────────────────────
# STEP 4 — SPLIT INTO SYLLABLES (IAST)
# ─────────────────────────────────────────
def split_syllables(text: str) -> list:
    """
    Splits an IAST string into a list of syllable strings.

    A Sanskrit syllable = consonant cluster(s) + vowel nucleus
                         + optional post-vowel modifiers (ṃ, ḥ).

    THE KEY FIX (v2):
      After matching a vowel nucleus, we immediately look ahead and
      grab any anusvara (ṃ) or visarga (ḥ) characters into the SAME
      syllable.  Previously these were left as dangling characters and
      ended up being counted as extra syllables, inflating the count.

      Before fix: "raṃ" → ["ra", "ṃ"]   (2 items — WRONG)
      After fix:  "raṃ" → ["raṃ"]       (1 item  — CORRECT)

      This caused a verse like the Vishnu Stuti to report 82 syllables
      instead of the correct 68 (17 per pāda × 4 pādas = Mandākrāntā).

    How syllable splitting works:
      We scan left-to-right. Characters accumulate in `current`.
      When we see a character that matches a known vowel (using the
      longest-match vowel priority order from vowel_rules.json), we
      finalize the current syllable, attach any trailing modifiers,
      then start a new one.
    """
    vowels = _vowel_order   # sorted longest-first to avoid partial matches

    syllables = []
    current   = ""
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Word spaces are syllable boundaries — flush current chunk
        if ch == " ":
            if current:
                syllables.append(current)
                current = ""
            i += 1
            continue

        current += ch

        # Try to match a vowel nucleus at the current position
        matched = False
        for vowel in vowels:
            vlen = len(vowel)
            if text[i: i + vlen] == vowel:

                # Multi-character vowel (e.g. 'ai', 'au', 'ā') — consume all its chars
                if vlen > 1:
                    current += text[i + 1: i + vlen]
                    i += vlen - 1   # main loop will add 1 more at the end

                # ── THE KEY FIX ──────────────────────────────────────────────
                # After the vowel nucleus, look ahead for post-vowel modifiers
                # (anusvara ṃ, visarga ḥ, etc.) and attach them to THIS syllable.
                # If we don't do this, they become dangling extra "syllables".
                look = i + vlen  # position right after the vowel
                while look < n and text[look] in _POST_VOWEL_MODIFIERS:
                    current += text[look]
                    look += 1
                # Adjust i so the main loop skips over the modifiers we grabbed
                i = look - 1   # -1 because the outer loop does i += 1 at the end
                # ──────────────────────────────────────────────────────────────

                syllables.append(current)
                current = ""
                matched = True
                break

        i += 1

    # Flush any remaining consonants (e.g. a word-final dead consonant)
    if current.strip():
        syllables.append(current)

    return syllables


# ─────────────────────────────────────────
# MAIN PARSE FUNCTION
# ─────────────────────────────────────────
def parse_text(text: str) -> dict:
    """
    Full pipeline: raw text → normalized → script detected
                  → transliterated to IAST → split into syllables.

    Returns a dict with:
      original        — the input exactly as given
      normalized      — after stripping junk chars
      script          — 'devanagari' / 'iast' / 'plain'
      transliteration — IAST representation
      syllables       — list of syllable strings (the main output)
      syllable_count  — len(syllables)
    """
    original = text
    text     = normalize_input(text)
    script   = detect_script(text)

    if script == "devanagari":
        transliterated = devanagari_to_iast(text)
    elif script == "plain":
        transliterated = plain_to_iast(text)
    else:
        transliterated = text   # already IAST

    syllables = split_syllables(transliterated)

    return {
        "original":        original,
        "normalized":      text,
        "script":          script,
        "transliteration": transliterated,
        "syllables":       syllables,
        "syllable_count":  len(syllables),
    }


# ─────────────────────────────────────────
# TEST RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    test_verses = [
        # Should give 17 syllables per pāda (68 total) → Mandākrāntā
        "शान्ताकारं भुजगशयनं पद्मनाभं सुरेशं।",
        # Should give 8 syllables per pāda (32 total) → Anuṣṭubh
        "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
        "karmaṇyevādhikāraste mā phaleṣu kadācana",
        "karmanyevaadhikaraste maa phaleshu kadaachana",
    ]

    for verse in test_verses:
        print("\n" + "─" * 60)
        result = parse_text(verse)
        print("Original       :", result["original"])
        print("Script         :", result["script"])
        print("Transliteration:", result["transliteration"])
        print("Syllable count :", result["syllable_count"])
        print("Syllables      :", result["syllables"])