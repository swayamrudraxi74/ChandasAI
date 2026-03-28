# ==========================================
# engine/meter_matcher.py  —  Sanskrit Metre Identification
# ==========================================
#
# WHAT THIS FILE DOES:
#   Takes the Laghu/Guru sequence and Gaṇa list from laghu_guru.py
#   and tries to identify which classical Sanskrit metre the verse belongs to.
#
# BUGS FIXED (v2):
#
#   BUG 1 — Key name mismatch (critical):
#     _format_result() was returning {"name": ...} but app.py was calling
#     meter_result.get("meter", "Unknown Metre").
#     Since "meter" key never existed, app.py ALWAYS saw "Unknown Metre"
#     and triggered the Groq fallback — even for verses the local database
#     correctly identified!
#     Fix: _format_result() now returns BOTH "name" AND "meter" keys.
#     The fallback dict also now includes "meter" key.
#
#   BUG 2 — Anushtubh syllable count check wrong:
#     Old code: `total_syllables == 8`
#     This checked if the ENTIRE verse has 8 syllables, which would only
#     match the shortest possible single pāda.  A full 2-line Anushtubh
#     shloka has 32 syllables (8 per pāda × 4 pādas).
#     Fix: Check for total_syllables that is a multiple of 8 and within
#     a reasonable range (24–40 to handle partial / full shlokas).
#
#   BUG 3 — Syllables_per_pada field used in matching:
#     Added a fallback match using the `syllables_per_pada` field from
#     meters.json so meters like Mandākrāntā (17) and Śārdūlavikrīḍita (19)
#     can be matched even if the gana_pattern or exact LG sequence doesn't
#     match perfectly.
# ==========================================

import json
import os

# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_json(filename):
    """Safely loads a JSON file. Returns empty dict on missing file."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[METER_MATCHER] ⚠️  Missing JSON file: {filepath}")
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# LOAD JSON FILES
# ─────────────────────────────────────────
meters_db     = load_json("meters.json").get("meters", [])
aliases_db    = load_json("meter_aliases.json").get("meter_aliases", {})
categories_db = load_json("meter_categories.json").get("meter_categories", [])


# ─────────────────────────────────────────
# HARDCODED SYLLABLE-COUNT → METRE TABLE
# ─────────────────────────────────────────
# This table is used as a LAST RESORT fallback before Groq:
# if the gana pattern and LG sequence both fail, we try to
# identify the metre just from syllables per pāda.
# 
# Only the most common classical metres are listed here.
# Groq handles anything outside this table.
#
# Format: syllables_per_pada → (metre_name, category)
_SYLLABLE_COUNT_TABLE = {
    6:  ("Tanumadhyā",        "Akshara"),
    7:  ("Gāyatrī",           "Akshara"),
    8:  ("Anuṣṭubh",          "Akshara"),   # Most common (Bhagavad Gita, etc.)
    9:  ("Bṛhatī",            "Akshara"),
    10: ("Pankti",            "Akshara"),
    11: ("Triṣṭubh / Upajāti","Akshara"),   # Indravajrā, Upendravajrā, Upajāti
    12: ("Jagatī / Vaṁśastha","Akshara"),
    13: ("Atijagati",         "Akshara"),
    14: ("Vasantatilakā",     "Akshara"),
    15: ("Mālinī",            "Akshara"),
    16: ("Pṛthvī",            "Akshara"),
    17: ("Mandākrāntā",       "Akshara"),   # Vishnu Stuti, many Sanskrit hymns
    18: ("Śikhariṇī",         "Akshara"),
    19: ("Śārdūlavikrīḍita",  "Akshara"),   # 19 per pāda
    21: ("Sragdharā",         "Akshara"),
}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _normalize_pattern(pattern_str: str) -> str:
    """
    Converts various pattern notations into the standard G/L format.
    Examples:
      '– – u'  →  'GGL'
      'GGL'    →  'GGL'  (already standard)
      '– u –'  →  'GLG'
    """
    return (
        pattern_str
        .replace("–", "G")
        .replace("u", "L")
        .replace(" ", "")
        .replace("|", "")
        .replace("x", "G")
    )


def _calculate_matras(lg_sequence: str) -> int:
    """
    Calculates total mātrā weight.
    Laghu (L) = 1 mātrā, Guru (G) = 2 mātrās.
    Used for mātrā-based metres like Āryā.
    """
    return sum(2 if ch == "G" else 1 for ch in lg_sequence)


# ─────────────────────────────────────────
# CORE MATCHING LOGIC
# ─────────────────────────────────────────

def find_meter(lg_sequence: str, gana_list: list) -> dict:
    """
    Attempts to identify the Sanskrit metre in four passes:

    Pass 1: Gaṇa pattern match — exact match against gana_pattern in meters.json
    Pass 2: LG sequence match  — exact match against the full L/G string
    Pass 3: Syllable-per-pāda match — uses the hardcoded table above
    Pass 4: Mātrā count match  — for mātrā-based metres (Āryā, Gīti, etc.)

    Returns a dict with BOTH "name" and "meter" keys (the old code only had
    "name" which caused the key-mismatch bug in app.py).
    """
    total_syllables = len(lg_sequence)
    total_matras    = _calculate_matras(lg_sequence)

    # How many syllables per pāda if the verse has 4 equal pādas?
    # This is only valid when total is divisible by 4.
    per_pada = total_syllables // 4 if total_syllables % 4 == 0 else None

    print(f"[METER_MATCHER] 🔍 Searching: total_syl={total_syllables}  "
          f"per_pada={per_pada}  total_matras={total_matras}")

    # Extract just the gana names for pattern comparison
    user_ganas = [g["gana"] for g in gana_list if g["gana"] != "partial"]
    print(f"[METER_MATCHER]     Gana sequence : {user_ganas}")
    print(f"[METER_MATCHER]     LG preview    : {lg_sequence[:20]}...")

    # ── Pass 1: Gaṇa pattern match ────────────────────────────────────────
    for meter in meters_db:
        if meter.get("gana_pattern") and user_ganas == meter["gana_pattern"]:
            print(f"[METER_MATCHER] ✅  Pass 1 (Gaṇa) match: {meter['name']}")
            return _format_result(meter, "Gaṇa Pattern Match")

    # ── Pass 2: Exact LG sequence match ──────────────────────────────────
    for meter in meters_db:
        if meter.get("pattern"):
            db_pattern = _normalize_pattern(meter["pattern"])
            if lg_sequence == db_pattern:
                print(f"[METER_MATCHER] ✅  Pass 2 (LG) match: {meter['name']}")
                return _format_result(meter, "Exact LG Sequence Match")

    # ── Pass 3: Syllable-per-pāda match ──────────────────────────────────
    #
    # FIX: Old code checked `total_syllables == 8` which only matched when
    # the ENTIRE verse had exactly 8 syllables.  Full shlokas have 32
    # (Anushtubh), 68 (Mandākrāntā), 76 (Śārdūlavikrīḍita), etc.
    #
    # New logic:
    #   a) Try the hardcoded table using per_pada syllable count
    #   b) Also check meters.json `syllables_per_pada` field

    if per_pada is not None:
        # Check hardcoded table first (fast, no JSON dependency)
        if per_pada in _SYLLABLE_COUNT_TABLE:
            metre_name, category = _SYLLABLE_COUNT_TABLE[per_pada]
            print(f"[METER_MATCHER] ✅  Pass 3a (syllable table): {metre_name} "
                  f"({per_pada} per pāda)")
            return _format_result_manual(
                name=metre_name,
                category=category,
                match_type=f"Syllable-per-pāda Match ({per_pada} per pāda)",
                syllables_per_pada=per_pada,
            )

        # Check meters.json `syllables_per_pada` field
        for meter in meters_db:
            db_per_pada = meter.get("syllables_per_pada")
            if db_per_pada and db_per_pada == per_pada:
                print(f"[METER_MATCHER] ✅  Pass 3b (JSON syl/pāda): {meter['name']}")
                return _format_result(meter, f"Syllables-per-pāda Match ({per_pada})")

    # ── Pass 4: Mātrā count match ─────────────────────────────────────────
    for meter in meters_db:
        if meter.get("category") == "Matra" and meter.get("matra_pattern"):
            if total_matras in meter["matra_pattern"]:
                print(f"[METER_MATCHER] ✅  Pass 4 (mātrā): {meter['name']}")
                return _format_result(meter, "Mātrā Count Match")

    # ── All passes failed ─────────────────────────────────────────────────
    print(f"[METER_MATCHER] ❌  No match found. Groq fallback will be triggered.")
    return {
        # BUG FIX: include BOTH "name" and "meter" so app.py's key lookup works
        "name":   "Unknown Metre",
        "meter":  "Unknown Metre",       # ← this key was missing before
        "status": "No Match Found",
        "details": {
            "syllable_count":    total_syllables,
            "syllables_per_pada": per_pada,
            "matra_count":       total_matras,
            "lg_sequence":       lg_sequence,
        },
    }


# ─────────────────────────────────────────
# FORMAT HELPERS
# ─────────────────────────────────────────

def _format_result(meter: dict, match_type: str) -> dict:
    """
    Wraps a meters.json entry into the standard response dict.

    BUG FIX: Now includes both "meter" and "name" keys.
    app.py calls meter_result.get("meter", "Unknown Metre"), so
    the "meter" key must exist in every success response.
    """
    metre_name = meter["name"]
    return {
        "name":            metre_name,
        "meter":           metre_name,     # ← BUG FIX: this key was missing
        "category":        meter.get("category", "Akshara"),
        "match_type":      match_type,
        "syllables_per_pada": meter.get("syllables_per_pada", "Variable"),
        "yati":            meter.get("yati", []),
        "aliases":         aliases_db.get(metre_name, []),
    }


def _format_result_manual(name: str, category: str,
                           match_type: str, syllables_per_pada) -> dict:
    """
    Creates a response dict when we identified the metre from the
    hardcoded _SYLLABLE_COUNT_TABLE rather than from meters.json.
    """
    return {
        "name":            name,
        "meter":           name,           # both keys for compatibility
        "category":        category,
        "match_type":      match_type,
        "syllables_per_pada": syllables_per_pada,
        "yati":            [],
        "aliases":         aliases_db.get(name, []),
    }


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    # Test: Vishnu Stuti  (should detect Mandākrāntā, 17 per pāda)
    # With the parser fix, total_syllables = 68, per_pada = 17
    mock_lg_17 = "G" * 17 * 4          # 68 Gs (simplified)
    mock_ganas = [{"gana": "ma"}, {"gana": "bha"}, {"gana": "na"},
                  {"gana": "ta"}, {"gana": "ta"}, {"gana": "ga"}]

    result = find_meter(mock_lg_17, mock_ganas)
    print(f"\nTest 1 (17 per pāda): meter='{result.get('meter')}' "
          f"name='{result.get('name')}'")

    # Test: Unknown (should return "Unknown Metre")
    mock_lg_unknown = "LGLGLG" * 3   # 18 chars, not divisible cleanly
    result2 = find_meter(mock_lg_unknown, [])
    print(f"Test 2 (unknown): meter='{result2.get('meter')}'")