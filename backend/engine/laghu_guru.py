import json
import os

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
# LOAD JSON FILES
# ─────────────────────────────────────────
vowel_rules     = load_json("vowel_rules.json")
consonant_rules = load_json("consonant_rules.json")
ganas_data      = load_json("ganas.json")

# ─────────────────────────────────────────
# BUILD LOOKUP TABLES
# ─────────────────────────────────────────

# From vowel_rules.json
_short_vowels   = set(vowel_rules["short_vowels"])   # a i u ṛ ḷ
_long_vowels    = set(vowel_rules["long_vowels"])     # ā ī ū ṝ e ai o au
_vowel_order    = vowel_rules["vowel_priority_order"] # longest-first

# From consonant_rules.json
_guru_clusters  = consonant_rules["guru_causing_clusters"]  # tr, kṣ, str ...
_anusvara       = consonant_rules["anusvara_and_visarga"]["anusvara"]  # ṃ
_visarga        = consonant_rules["anusvara_and_visarga"]["visarga"]   # ḥ

# From ganas.json
_pattern_to_gana = ganas_data["lookup_by_pattern"]   # "GGL" → "ta"
_gana_details    = {g["name"]: g for g in ganas_data["ganas"]}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _extract_vowel(syllable: str) -> str | None:
    """Find the vowel nucleus inside a syllable string."""
    for v in _vowel_order:           # longest-first so 'ai' beats 'a'
        if v in syllable:
            return v
    return None


def _starts_with_cluster(text: str) -> bool:
    """Check if text starts with a guru-causing consonant cluster."""
    for cluster in sorted(_guru_clusters, key=len, reverse=True):
        if text.startswith(cluster):
            return True
    return False


# ─────────────────────────────────────────
# CORE: CLASSIFY ONE SYLLABLE
# ─────────────────────────────────────────

def classify_syllable(syllable: str, next_syllable: str = "") -> str:
    """
    Returns 'G' (guru) or 'L' (laghu) for a single IAST syllable.

    Rules (in priority order):
    1. Long vowel → always G
    2. Anusvara (ṃ) anywhere → G
    3. Visarga (ḥ) anywhere → G
    4. Short vowel followed by consonant cluster in next syllable → G
    5. Short vowel alone → L
    """
    syllable = syllable.strip()

    # Rule 2 — anusvara makes it guru
    if _anusvara in syllable:
        return "G"

    # Rule 3 — visarga makes it guru
    if _visarga in syllable:
        return "G"

    vowel = _extract_vowel(syllable)

    if vowel is None:
        # No vowel found — treat as consonant-only tail, guru by convention
        return "G"

    # Rule 1 — long vowel always guru
    if vowel in _long_vowels:
        return "G"

    # Short vowel from here on
    # Rule 4 — short vowel + next syllable starts with cluster → guru by position
    if next_syllable and _starts_with_cluster(next_syllable):
        return "G"

    # Rule 5 — short vowel, no heavy following → laghu
    return "L"


# ─────────────────────────────────────────
# CLASSIFY FULL SYLLABLE LIST → LG STRING
# ─────────────────────────────────────────

def get_lg_sequence(syllables: list) -> str:
    """
    Takes syllable list from parser.py and returns LG string.
    e.g. ['ka', 'rma', 'ṇye', 'vā'] → 'LGGG'
    """
    lg = []
    n = len(syllables)

    for i, syl in enumerate(syllables):
        next_syl = syllables[i + 1] if i + 1 < n else ""
        lg.append(classify_syllable(syl, next_syl))

    return "".join(lg)


# ─────────────────────────────────────────
# GROUP LG STRING INTO GANAS
# ─────────────────────────────────────────

def get_ganas(lg_sequence: str) -> list:
    """
    Groups LG string into gana triplets and looks up each in ganas.json.
    e.g. 'GGGLLG' → [{'pattern':'GGG','gana':'ma'}, {'pattern':'LLG','gana':'sa'}]
    """
    group_size = ganas_data["processing_rules"]["group_size"]  # 3
    groups = []
    i = 0

    while i < len(lg_sequence):
        chunk = lg_sequence[i:i + group_size]
        gana_name = _pattern_to_gana.get(chunk, None)
        groups.append({
            "pattern": chunk,
            "gana":    gana_name if gana_name else "partial"
        })
        i += group_size

    return groups


# ─────────────────────────────────────────
# MAIN FUNCTION — called by meter_matcher
# ─────────────────────────────────────────

def analyze(syllables: list) -> dict:
    """
    Input  : syllable list from parse_text()
    Output : {
        "syllables"    : [...],
        "lg_sequence"  : "GLGGLG...",
        "ganas"        : [{"pattern":"GGL","gana":"ta"}, ...],
        "syllable_count": 16
    }
    """
    lg_sequence = get_lg_sequence(syllables)
    ganas       = get_ganas(lg_sequence)

    return {
        "syllables":     syllables,
        "lg_sequence":   lg_sequence,
        "ganas":         ganas,
        "syllable_count": len(syllables),
    }


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from parser import parse_text

    test_verses = [
        "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
        "karmaṇyevādhikāraste mā phaleṣu kadācana",
        "इन्द्रस्य वज्र इव दृढशक्तिरस्तु",
    ]

    for verse in test_verses:
        print("\n" + "─" * 60)
        parsed  = parse_text(verse)
        result  = analyze(parsed["syllables"])

        print("Verse      :", verse)
        print("Syllables  :", result["syllables"])
        print("L/G        :", result["lg_sequence"])
        print("Ganas      :", [(g["pattern"], g["gana"]) for g in result["ganas"]])
        print("Count      :", result["syllable_count"])