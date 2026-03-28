# ==========================================
# api/app.py  —  ChandasAI FastAPI Backend
# ==========================================
#
# WHAT CHANGED (v3):
#
#   BUG FIX 1 — Key lookup for metre name:
#     meter_result.get("meter", ...) now also falls back to "name" key.
#     This makes app.py robust to either old or new meter_matcher output.
#
#   IMPROVEMENT 1 — Groq metre-detection prompt:
#     Added a complete lookup table of classical Sanskrit metres with their
#     syllable-per-pāda counts.  Previously only 3 metres were listed
#     (Anuṣṭubh/32, Upajāti/44, Vaṁśastha/48), so Mandākrāntā (68),
#     Śārdūlavikrīḍita (76), Vasantatilakā (56), etc. always triggered
#     a wrong Groq guess.
#
#   IMPROVEMENT 2 — CMD logging:
#     Every step now prints a clear, organized log line so you can watch
#     the full analysis pipeline in the backend terminal.
#
#   IMPROVEMENT 3 — Waveform crash guard:
#     samples_per_bar = max(1, len(y) // n_bars) prevents a division-by-zero
#     if the generated audio is very short.
# ==========================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys
import os
import time

import librosa
import numpy as np

from groq import Groq
from dotenv import load_dotenv

# Load GROQ_API_KEY from the .env file in the backend folder
load_dotenv()

import re
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
except ImportError:
    sanscript = None

def ensure_devanagari(text: str) -> str:
    """Detects English characters and auto-converts to Devanagari."""
    if re.search(r'[a-zA-Z]', text):
        if sanscript:
            print("  [TEXT] 🔠 English input detected. Auto-converting to Devanagari...")
            return transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
    return text

# Add the parent of api/ to sys.path so we can import engine.*
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.parser        import parse_text
from engine.laghu_guru    import analyze as analyze_lg
from engine.meter_matcher import find_meter
from engine.recitation_helper import RecitationHelper

# ==========================================
# APP SETUP
# ==========================================
app = FastAPI(title="ChandasAI Backend Engine")

# CORS: allows the React frontend (Vite on port 5173) to reach this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize once at startup — avoids per-request latency
reciter      = RecitationHelper()
groq_client  = Groq(api_key=os.environ.get("GROQ_API_KEY"))
os.makedirs("static", exist_ok=True)


class VerseRequest(BaseModel):
    text: str


# ==========================================
# ENDPOINT 1: TEXT ANALYSIS
# ==========================================
@app.post("/analyze-text")
async def analyze_text_only(request: VerseRequest):
    print("\n" + "🟢" * 22)
    print(f"[API /analyze-text] Triggered")
    
    # 🛠️ FIX 1: Convert English to Devanagari IMMEDIATELY before doing any math!
    request.text = ensure_devanagari(request.text)
    print(f"  ↳ Input snippet : '{request.text[:60]}{'...' if len(request.text) > 60 else ''}'")

    try:
        print("\n  [STEP 1 & 2] 🔬 Classifying Laghu / Guru weights (Strict v6)...")
        
        # 🛠️ FIX 2: Use the flawless mathematical syllable engine
        aksharas = reciter.syllabify_pada(request.text)
        
        sequence = "".join([ak["lg"] for ak in aksharas])
        formatted_syllables = [{"text": ak["text"], "type": ak["lg"]} for ak in aksharas]
        
        guru_count  = sequence.count("G")
        laghu_count = sequence.count("L")
        syl_count   = len(aksharas)
        per_pada    = syl_count // 4 if syl_count % 4 == 0 else "N/A"
        
        print(f"           Syllables      : {syl_count}  (G={guru_count}  L={laghu_count})")
        print(f"           Per pāda       : {per_pada}")
        print(f"           LG sequence    : {sequence[:24]}...")

        # ── Step 3: Metre matching ─────────────────────────────────────────
        try:
            # We call the old parser purely to generate "ganas" for the DB lookup
            parsed_data = parse_text(request.text)
            lg_data = analyze_lg(parsed_data["syllables"])
            meter_result = find_meter(sequence, lg_data["ganas"])
            metre_name = meter_result.get("meter") or meter_result.get("name") or "Unknown Metre"
        except Exception:
            metre_name = "Unknown Metre"

        # ── Step 4: Groq AI fallback ───────────────────────────────────────
        if metre_name in ("Unknown Metre", "Meter is not present in the database", "", None):
            print("\n  [STEP 4] 🤖 Local DB failed → triggering Groq AI fallback...")
            metre_name = _groq_metre_fallback(
                text=request.text,
                total_syl=syl_count,
                per_pada=per_pada,
            )

        print(f"\n  [API] ✅ Analysis complete → metre='{metre_name}'")
        print(f"  [API] 📤 Sending {len(formatted_syllables)} precise syllables to React.")

        return {
            "syllables":    formatted_syllables,
            "metre":        metre_name,
            "raw_sequence": sequence,
        }

    except Exception as e:
        print(f"\n  [API ERROR] ❌ /analyze-text crashed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────
# GROQ METRE FALLBACK HELPER
# ─────────────────────────────────────────
def _groq_metre_fallback(text: str, total_syl: int, per_pada) -> str:
    """
    Calls the Groq LLM to identify the metre when the local database
    cannot find a match.

    Provides a FULL lookup table of classical Sanskrit metres so Groq
    does not have to guess — it just needs to look up the syllable count.

    Previously only 3 metres were listed (Anuṣṭubh/32, Upajāti/44,
    Vaṁśastha/48).  This meant Mandākrāntā (68), Śārdūlavikrīḍita (76),
    Vasantatilakā (56), etc. were ALL guessed wrong by Groq.
    """
    print(f"  [GROQ] 🌐 Sending to llama-3.3-70b-versatile...")
    print(f"         Total syllables : {total_syl}")
    print(f"         Per pāda (÷4)   : {per_pada}")

    prompt = (
        f"You are an expert in classical Sanskrit prosody (Chandas).\n"
        f"Identify the metre of the following verse STRICTLY based on syllable counts.\n\n"
        f"Verse snippet:\n{text[:120]}\n\n"
        f"Syllable data:\n"
        f"  Total syllables       : {total_syl}\n"
        f"  Syllables per pāda (÷4): {per_pada}\n\n"
        "Complete metre lookup table — use syllables PER PĀDA:\n"
        "   6 per pāda (24 total)  → Tanumadhyā\n"
        "   7 per pāda (28 total)  → Gāyatrī\n"
        "   8 per pāda (32 total)  → Anuṣṭubh (Śloka)\n"
        "   9 per pāda (36 total)  → Bṛhatī\n"
        "  10 per pāda (40 total)  → Paṅkti\n"
        "  11 per pāda (44 total)  → Triṣṭubh / Upajāti / Indravajrā\n"
        "  12 per pāda (48 total)  → Jagatī / Vaṁśastha / Drutavilambita\n"
        "  13 per pāda (52 total)  → Atijagati\n"
        "  14 per pāda (56 total)  → Vasantatilakā\n"
        "  15 per pāda (60 total)  → Mālinī\n"
        "  16 per pāda (64 total)  → Pṛthvī\n"
        "  17 per pāda (68 total)  → Mandākrāntā\n"
        "  18 per pāda (72 total)  → Śikhariṇī\n"
        "  19 per pāda (76 total)  → Śārdūlavikrīḍita\n"
        "  21 per pāda (84 total)  → Sragdharā\n\n"
        "Rules:\n"
        "  1. Base your answer ONLY on the syllable count given above.\n"
        "  2. Do NOT try to read the Sanskrit text to guess the metre.\n"
        "  3. If the total is not divisible by 4, mention the closest match.\n"
        "  4. Respond with ONLY the metre name. Nothing else."
    )

    start = time.time()
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=20,   # We only need a short metre name
        )
        elapsed      = time.time() - start
        groq_metre   = completion.choices[0].message.content.strip()

        print(f"  [GROQ] ⏱️  Response in {elapsed:.2f}s")
        print(f"  [GROQ] ✅  Detected : '{groq_metre}'")
        return groq_metre if groq_metre else "Unknown Metre"

    except Exception as e:
        print(f"  [GROQ] ❌  API call failed: {e}")
        return "Unknown Metre"


# ==========================================
# ENDPOINT 2: AUDIO GENERATION
# ==========================================
@app.post("/generate-audio")
async def generate_audio_only(request: VerseRequest):
    """
    Generates a Sanskrit recitation WAV file.

    Pipeline (all inside RecitationHelper):
      1. Groq adds Yati (half-breath) commas where appropriate
      2. Text split by Dandas into individual lines
      3. Each line → Edge-TTS → audio array
      4. Lines stitched with correct pause lengths
      5. Temple reverb + Om drone applied
      6. Final WAV saved

    This endpoint then extracts 80 amplitude peaks from the WAV
    for the React waveform bar animation, and returns the audio URL.
    """
    print("\n" + "🟣" * 22)
    print(f"[API /generate-audio] Triggered")

    # Convert English to Devanagari for audio too
    request.text = ensure_devanagari(request.text)

    print(f"  Input length : {len(request.text)} chars")
    print(f"  Snippet      : '{request.text[:60]}{'...' if len(request.text) > 60 else ''}'")

    try:
        output_filename = "static/recitation.wav"

        # Cache busting: remove old WAV so browser can't play stale audio
        if os.path.exists(output_filename):
            os.remove(output_filename)
            print(f"  ↳ 🗑️  Old WAV deleted.")

        # ── Audio generation (full SPARSH-X pipeline) ──────────────────────
        print(f"\n  ↳ 🚀 Handing off to RecitationHelper pipeline...")
        gen_start = time.time()

        reciter.create_full_recitation(request.text, output_filename)

        gen_elapsed = time.time() - gen_start
        print(f"\n  ↳ ⏱️  RecitationHelper finished in {gen_elapsed:.2f}s")

        # Verify the file was actually created
        if not os.path.exists(output_filename):
            raise RuntimeError("RecitationHelper produced no output file.")

        file_kb = os.path.getsize(output_filename) / 1024
        print(f"  ↳ ✅  WAV confirmed: {output_filename} ({file_kb:.1f} KB)")

        # ── Waveform extraction for React bar chart ─────────────────────────
        # Load at native sample rate (sr=None keeps original)
        print(f"\n  [WAVEFORM] 🌊 Extracting 80 amplitude peaks for React UI...")
        y, sr = librosa.load(output_filename, sr=None)
        audio_duration = len(y) / sr
        print(f"  [WAVEFORM]    Loaded: {y.shape[0]} samples @ {sr}Hz ({audio_duration:.2f}s)")

        n_bars = 80

        # CRASH GUARD: max(1, ...) prevents division-by-zero on very short audio
        samples_per_bar = max(1, len(y) // n_bars)

        waveform_data = []
        for i in range(n_bars):
            start = i * samples_per_bar
            end   = min(start + samples_per_bar, len(y))
            if start >= len(y):
                waveform_data.append(0.0)   # pad with silence if audio shorter than 80 bars
            else:
                peak = float(np.max(np.abs(y[start:end])))
                waveform_data.append(peak)

        # Normalize to [0, 100] for CSS height values
        max_val = max(waveform_data) if max(waveform_data) > 0 else 1.0
        normalized_waveform = [(v / max_val) * 100 for v in waveform_data]

        print(f"  [WAVEFORM] ✅  Extracted {len(normalized_waveform)} bars  "
              f"(samples_per_bar={samples_per_bar}  peak={max_val:.4f})")

        # Timestamp in URL busts browser audio cache
        timestamp = int(time.time())
        print(f"\n  [API] 📤 Sending audio_url (t={timestamp}) + waveform to React.")

        return {
            "audio_url": f"http://127.0.0.1:8000/audio?t={timestamp}",
            "waveform":  normalized_waveform,
        }

    except Exception as e:
        print(f"\n  [API ERROR] ❌ /generate-audio crashed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINT 3: AUDIO FILE SERVING
# ==========================================
@app.get("/audio")
async def get_audio():
    """
    Streams the final WAV to the React <audio> element.
    Cache-Control headers prevent the browser from replaying stale audio.
    """
    print(f"\n  [AUDIO] 🎧 Browser requested recitation.wav")
    audio_path = "static/recitation.wav"

    if not os.path.exists(audio_path):
        print(f"  [AUDIO] ❌ File not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found.")

    file_kb = os.path.getsize(audio_path) / 1024
    print(f"  [AUDIO] ✅ Streaming {audio_path} ({file_kb:.1f} KB)")

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 55)
    print("🕉️  CHANDAS-AI BACKEND  —  SPARSH-X Engine v5.5+")
    print("     Listening on  http://127.0.0.1:8000")
    print("=" * 55 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000)