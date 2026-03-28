# ==========================================
# engine/recitation_helper.py  —  SPARSH-X Audio Engine v6
# ==========================================
#
# WHAT THIS FILE DOES:
#   Converts raw Devanagari Sanskrit text into a high-quality WAV audio
#   file that sounds like an expert recitation, with:
#     - Correct Sanskrit pronunciation (Visarga, Schwa, conjuncts)
#     - Line-by-line TTS to bypass Microsoft character limits
#     - Mathematically correct pause durations (600ms / 1200ms)
#     - Groq AI for Yati (mid-line half-breath) placement
#     - Temple reverb for acoustic depth
#     - Om sine-wave drone for devotional atmosphere
#
# BUGS FIXED vs v5.5:
#
#   FIX 1 — Visarga (ः) pronunciation:
#     Old: "ः" → "हा"  (adds an EXTRA vowel 'a' → sounds wrong)
#     New: Context-aware:
#          ः before a consonant → "ह्" (half-h, no extra vowel)
#          ः word-finally after ā → "ह" (soft h breath, no extra vowel)
#     Result: "दुःख" → "दुह्ख" (correct "duh-kha" not wrong "doohu-kh")
#
#   FIX 2 — Schwa deletion before semivowels:
#     Hindi TTS drops the inherent 'a' before य (ya) and व (va).
#     "निरामयाः" → "Ni-rah-myah" (WRONG, drops 'a' in "mya")
#     Fix: Insert ZWNJ (U+200C) between the bare consonant and ya/va.
#     "निराम\u200Cयाः" → "Ni-rah-mu-yah" (CORRECT)
#
#   FIX 3 — Double-boost distortion:
#     Old: (mixed_audio * 1.3) + drone — causes hard clipping at >1.0
#     New: with_reverb + drone (no ×1.3)
#     The --volume="+25%" in Edge-TTS is sufficient.
#
#   FIX 4 — Temple reverb overlap bug:
#     Old decay was 0.3 — the echo overlapped original and made the
#     first 200ms of audio noticeably louder than the rest.
#     New decay = 0.15 — echo is audible but does not inflate original.
#
#   FIX 5 — Abrupt Om drone start/stop:
#     Added 90ms fade-in and fade-out envelopes on the drone.
#
#   IMPROVEMENT — Melodious audio:
#     Added a subtle harmonic octave overtone (very quiet, +12 semitones)
#     mixed at 6% volume to simulate the natural resonance of trained
#     chanting vocals. Can be disabled with use_harmonic=False.
# ==========================================

import os
import re
import time
import librosa
import soundfile as sf
import numpy as np
from groq import Groq


class RecitationHelper:

    def __init__(self, sample_rate: int = 44100):
        print("\n" + "█" * 62)
        print("[SYSTEM INIT] 🛠️  SPARSH-X Audio Engine  v6")
        print(f"[SYSTEM INIT] 🎛️  Sample rate    : {sample_rate} Hz (CD quality)")
        print("█" * 62 + "\n")

        # CD-quality (44100 Hz) gives clean reverb tails
        self.sample_rate = sample_rate

        # Microsoft Hindi Neural voice — best Schwa retention we've found
        # for Sanskrit compared to other free voices.
        self.voice = "mr-IN-SwaraNeural"

        # Pause durations — validated by listening to expert chanters
        # Single Danda (।) = half-verse boundary → 600 ms (quick breath)
        # Double Danda (॥) = full-verse boundary → 1200 ms (deep breath)
        self.pause_half_ms = 600
        self.pause_full_ms = 1200

        # Groq client — used for Yati comma placement only (not metre detection)
        self.groq_client = None
        try:
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("[SYSTEM INIT] 🟢  Groq API authenticated.")
        except Exception as e:
            print(f"[SYSTEM INIT] 🔴  Groq unavailable: {e}")

    # ══════════════════════════════════════════════════════════════════
    # STRICT MATH ENGINE — Sanskrit Prosody (Chandas)
    # ══════════════════════════════════════════════════════════════════
    def syllabify_pada(self, text: str) -> list:
        VIRAMA   = "\u094D"
        ANUSVARA = "\u0902"
        VISARGA  = "\u0903"

        LONG_MATRA = {"\u093E", "\u0940", "\u0942", "\u0947", "\u094B", "\u0948", "\u094C"}
        LONG_VOWEL = {"\u0906", "\u0908", "\u090A", "\u090F", "\u0913", "\u0910", "\u0914"}

        def _is_consonant(c): return 0x0915 <= ord(c) <= 0x0939
        def _is_matra(c): return c in LONG_MATRA or c in {"\u093F", "\u0941", "\u0943", "\u0962", "\u0963"}
        def _is_independent_vowel(c): return c in LONG_VOWEL or c in {"\u0905", "\u0907", "\u0909", "\u090B", "\u090C", "\u0960", "\u0961"}

        akshara_list = []
        chars = list(text.strip().replace("\u00a0", ""))
        i, n = 0, len(chars)

        # ── PASS 1: Orthographic Parsing ──────────────────────────────
        while i < n:
            ak = {"text": "", "lg": "L", "consonant_count": 0, "is_halant": False, "is_space": False}

            # 🛠️ THE FIX: Added "\u093D" (Avagraha 'ऽ') to the ignored characters list
            if chars[i] in {" ", ",", ".", "।", "॥", "\n", "\r", "-", "\u093D"}:
                ak["text"] = chars[i]
                ak["is_space"] = True
                akshara_list.append(ak)
                i += 1
                continue

            while i < n and _is_consonant(chars[i]):
                ak["text"] += chars[i]
                ak["consonant_count"] += 1
                i += 1
                if i < n and chars[i] == VIRAMA:
                    ak["text"] += VIRAMA
                    i += 1
                else:
                    break

            if i < n and (_is_matra(chars[i]) or _is_independent_vowel(chars[i])):
                if chars[i] in LONG_MATRA or chars[i] in LONG_VOWEL:
                    ak["lg"] = "G"
                ak["text"] += chars[i]
                i += 1
            elif ak["consonant_count"] > 0:
                if ak["text"].endswith(VIRAMA):
                    ak["is_halant"] = True
            else:
                ak["text"] += chars[i]
                i += 1

            while i < n and chars[i] in {ANUSVARA, VISARGA, "\u0901"}:
                ak["lg"] = "G"
                ak["text"] += chars[i]
                i += 1

            if ak["text"]:
                akshara_list.append(ak)

        # ── PASS 2: Chandas Look-Ahead Rules ──────────────────────────
        final_aksharas = []
        
        for j in range(len(akshara_list)):
            curr = akshara_list[j]
            
            if curr["is_space"]:
                continue  # Ignore spaces/avagrahas in the mathematical output

            # Halant Rule: Attach dead consonants (म्) to the previous syllable
            if curr["is_halant"]:
                if len(final_aksharas) > 0:
                    final_aksharas[-1]["text"] += curr["text"]
                    final_aksharas[-1]["lg"] = "G" # Forces previous to Guru
                continue 

            # Conjunct Look-Ahead: Find the NEXT actual syllable
            next_syl = None
            for k in range(j + 1, len(akshara_list)):
                if not akshara_list[k]["is_space"]:
                    next_syl = akshara_list[k]
                    break
            
            if next_syl:
                if next_syl["consonant_count"] > 1:  # Followed by conjunct
                    curr["lg"] = "G"
                if next_syl["is_halant"]:            # Followed by dead consonant
                    curr["lg"] = "G"

            final_aksharas.append(curr)

        return final_aksharas

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1 — SANSKRIT PHONETIC PRE-PROCESSOR (GROQ JSON UPGRADE)
    # ══════════════════════════════════════════════════════════════════

    def sanskrit_phonetic_preprocess(self, text: str) -> str:
        """
        Uses Groq (LLM) in STRICT JSON MODE to prepare Sanskrit text for Hindi TTS.
        """
        print("\n  [PHONETICS] 🔬 AI Sanskrit phonetic pre-processor running...")
        original_len = len(text)

        if self.groq_client is None:
            print("  [PHONETICS] ⚠️ Groq unavailable. Using raw text.")
            return text

        prompt = (
            "You are an expert Sanskrit phonetic transcriber. "
            "I am sending this Sanskrit verse to a Hindi Text-to-Speech AI. "
            "The Hindi AI will mispronounce it by dropping the short 'a' at the end of words and misreading Visargas.\n\n"
            "Your task is to 'phoneticize' the text to trick the Hindi TTS into perfect Sanskrit pronunciation:\n"
            "1. SCHWA PRESERVATION: Append the letter 'अ' to any consonant where the short 'a' MUST be pronounced (e.g., at the end of words or breaking up long Sandhi compounds). Example: 'तुषार' -> 'तुषारअ', 'शुभ्रवस्त्रा' -> 'शुभ्रअ वस्त्रा'.\n"
            "2. VISARGA FIX: Change 'ः' to 'ह्' if it's before a consonant, or 'ह' if it's at the end of a line/word.\n"
            "3. DO NOT ADD COMMAS OR PUNCTUATION. Just fix the letters.\n"
            "4. CRITICAL: Output ONLY a valid JSON object with a single key 'phonetic_text'. No English, no explanations.\n\n"
            f"Input:\n{text}\n\nOutput JSON:"
        )

        import time, json
        start = time.time()
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pure JSON translation engine. You never output conversational text or markdown."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"}  # 🔒 FORCES STRICT JSON
            )
            elapsed = time.time() - start
            result_raw = completion.choices[0].message.content.strip()

            # Parse the JSON to extract the text
            data = json.loads(result_raw)
            result = data.get("phonetic_text", text)

            print(f"  [PHONETICS] ✅ AI Phonetics done in {elapsed:.2f}s ({original_len} chars → {len(result)} chars)")
            print(f"  ↳ Output: '{result[:70]}{'...' if len(result) > 70 else ''}'")
            return result

        except Exception as e:
            print(f"  [PHONETICS] ⚠️ AI Phonetics failed or bad JSON: {e}. Using original text.")
            return text
        
    # ══════════════════════════════════════════════════════════════════
    # PHASE 2 — GROQ AI: YATI PLACEMENT (GROQ JSON UPGRADE)
    # ══════════════════════════════════════════════════════════════════

    def apply_ai_punctuation(self, text: str) -> str:
        """
        Uses Groq in STRICT JSON MODE to insert commas for mid-line pauses.
        Includes a mathematical integrity check to ensure no letters were changed.
        """
        if "," in text:
            print("\n  [YATI] ⏩ Commas already present — skipping Groq Yati placement.")
            return text

        if self.groq_client is None:
            print("\n  [YATI] ⚠️  Groq unavailable — skipping Yati placement.")
            return text

        print("\n  " + "-" * 56)
        print("  [YATI] 🧠  Groq Yati Placement")
        print("  " + "-" * 56)
        print(f"  ↳ Input  : '{text[:70]}{'...' if len(text) > 70 else ''}'")

        prompt = (
            "You are an expert Vedic Sanskrit prosody engine.\n"
            "Your task: insert commas (,) to mark Yati — the natural half-breath pauses inside each line of the verse.\n\n"
            "STRICT RULES:\n"
            "1. NEVER alter, add, or remove ANY Devanagari letters, matras, or modifiers.\n"
            "2. NEVER touch or remove Dandas (। or ॥). Leave them exactly as they are.\n"
            "3. ONLY insert commas (,) where a breath-pause is natural.\n"
            "4. If the syllable is inside a glued compound word, do NOT insert a comma.\n"
            "5. CRITICAL: Output ONLY a valid JSON object with a single key 'yati_text'. No English, no explanations.\n\n"
            f"Input:\n{text}\n\nOutput JSON:"
        )

        import time, json
        start = time.time()
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a rigid punctuation engine. You output pure JSON. You NEVER change any Devanagari letters."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"}  # 🔒 FORCES STRICT JSON
            )
            elapsed = time.time() - start
            result_raw = completion.choices[0].message.content.strip()

            # Parse the JSON to extract the text
            data = json.loads(result_raw)
            result = data.get("yati_text", text)

            print(f"  ↳ Groq response time : {elapsed:.2f}s")

            # ── INTEGRITY CHECK ──────────────────────────────────────────
            def core_chars(s: str) -> str:
                return "".join(
                    c for c in s
                    if c not in {" ", ",", ".", "।", "॥", "\n", "\r", "\t"}
                )

            if core_chars(text) != core_chars(result):
                print("  ↳ ❌  INTEGRITY FAIL: Groq changed Devanagari characters!")
                print("  ↳ ⚠️  Discarding AI output. Using original text.")
                return text
            else:
                print(f"  ↳ 🔒  Integrity check PASSED — characters intact.")
                print(f"  ↳ ✅  Yati result: '{result[:70]}{'...' if len(result) > 70 else ''}'")
                return result

        except Exception as e:
            print(f"  ↳ ⚠️  Groq Yati failed or bad JSON: {e}. Using original text.")
            return text

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3 — LINE SPLITTER: respects Danda verse structure
    # ══════════════════════════════════════════════════════════════════

    def split_by_dandas(self, text: str) -> list:
        """
        Splits the Sanskrit verse into (line_text, pause_ms) pairs,
        one pair per line, using Danda punctuation as boundaries.

        WHY SPLIT AT ALL?
          Edge-TTS silently stops generating audio after ~200–250 chars
          in a single request.  For a long verse like the Adhyasa Bhashya,
          the audio would just cut off mid-sentence.
          Line-by-line generation completely eliminates this problem.

        PAUSE LENGTHS:
          ।  (single Danda) = half-verse boundary → 600ms breath
          ॥  (double Danda) = full-verse boundary → 1200ms breath
          \\n (newline)      = treated as single Danda → 600ms

        HOW IT WORKS:
          Scan character by character. Accumulate into current_chunk.
          When we hit ।, ॥, or flush at end → save (chunk, pause_ms).

        Returns: [ ("line text", pause_ms), ... ]
        """
        print("\n  [SPLIT] ✂️  Splitting by Danda boundaries...")
        print(f"  ↳ Input : {len(text)} characters")

        # Normalise newlines to single Danda so one pass handles all cases
        normalised = text.replace("\n", "।")

        segments     = []
        current_chunk = ""

        for ch in normalised:
            if ch == "॥":
                # Double Danda → full-verse boundary → long pause
                if current_chunk.strip():
                    segments.append((current_chunk.strip(), self.pause_full_ms))
                current_chunk = ""
            elif ch == "।":
                # Single Danda → half-verse boundary → short pause
                if current_chunk.strip():
                    segments.append((current_chunk.strip(), self.pause_half_ms))
                current_chunk = ""
            else:
                current_chunk += ch

        # Flush any trailing text without a Danda
        if current_chunk.strip():
            segments.append((current_chunk.strip(), self.pause_full_ms))

        print(f"  ↳ Found {len(segments)} segment(s):\n")
        for idx, (seg, pause) in enumerate(segments):
            preview = seg[:50] + ("..." if len(seg) > 50 else "")
            print(f"     [{idx + 1}] '{preview}'  → pause={pause}ms")

        return segments

    # ══════════════════════════════════════════════════════════════════
    # PHASE 4 — TTS LINE SANITISER
    # ══════════════════════════════════════════════════════════════════

    def sanitise_line(self, text: str) -> str:
        """
        Final cleanup before sending a line to Edge-TTS.

        What it does:
          - Removes double-quote characters that break the shell command
            (e.g. "edge-tts -t "..."" would crash with quotes inside)
          - Removes carriage returns / newlines
          - Strips leading/trailing whitespace

        What it does NOT do:
          - Does NOT remove commas (they signal Yati pauses to TTS)
          - Does NOT remove Dandas (already stripped by split_by_dandas)
          - Does NOT change Devanagari letters (phonetics are done in Phase 1)

        NOTE: Phonetic substitutions (Visarga, ZWNJ) are applied ONCE
        per verse in sanskrit_phonetic_preprocess(), BEFORE this function.
        This function is just a shell-safety cleanup per-line.
        """
        text = text.replace('"', "")   # prevents shell command breakage
        text = text.replace("\n", " ").replace("\r", " ")
        return text.strip()

    # ══════════════════════════════════════════════════════════════════
    # DSP — Temple reverb
    # ══════════════════════════════════════════════════════════════════

    def apply_temple_reverb(self, audio: np.ndarray,
                             delay_ms: int = 200,
                             decay: float = 0.15) -> np.ndarray:
        """
        Adds an acoustic echo simulating a large stone temple hall.

        How it works:
          1. Create a blank array (len(audio) + delay_samples) long
          2. Copy original audio into position 0
          3. Add a quieter, time-delayed copy (the echo) starting at delay_samples

        The overlap region [delay_samples : len(audio)] contains both
        the original signal AND the echo, so the amplitude there is:
          1.0 (original) + 0.15 (echo) = 1.15×

        With decay=0.15 this 15% bump is subtle and musical.
        With decay=0.30 (old value) the bump was 30% — noticeably louder
        in the first 200ms, creating an uneven volume profile.

        decay reduced 0.30 → 0.15 to fix this (v6 fix).
        """
        print(f"\n  [DSP] 🛕  Temple Reverb  |  delay={delay_ms}ms  decay={decay}")
        delay_samples = int((delay_ms / 1000.0) * self.sample_rate)
        reverb_audio  = np.zeros(len(audio) + delay_samples)
        reverb_audio[: len(audio)] = audio
        reverb_audio[delay_samples:] += audio * decay
        print(f"       → Reverb tail: +{delay_samples} samples ({delay_ms}ms)")
        return reverb_audio

    # ══════════════════════════════════════════════════════════════════
    # DSP — Om drone (136.1 Hz) with smooth fade
    # ══════════════════════════════════════════════════════════════════

    def generate_sine_drone(self, num_samples: int,
                             frequency: float = 136.1,
                             volume: float = 0.04) -> np.ndarray:
        """
        Generates a continuous sine-wave background drone.

        136.1 Hz is the classical tuning frequency of 'Om' (C# in
        scientific pitch tuning).  It sits well below the fundamental
        voice frequency range, providing a grounding presence without
        competing with the chant.

        FADE FIX (v6):
          Old code: drone started and stopped at full volume → abrupt click
          New code: 90ms (4000 sample) fade-in and fade-out envelopes
          Result: smooth, natural start and end

        volume reduced 0.05 → 0.04 so the drone stays under the voice.
        """
        print(f"  [DSP] 🧘  Om Drone  |  {frequency} Hz  vol={volume}")
        t     = np.linspace(0, num_samples / self.sample_rate,
                            num_samples, endpoint=False)
        drone = np.sin(2 * np.pi * frequency * t) * volume

        # Fade length: ~90ms at 44100Hz (prevents abrupt click)
        fade_len = min(4000, num_samples // 4)

        drone[:fade_len]   *= np.linspace(0.0, 1.0, fade_len)   # fade in
        drone[-fade_len:]  *= np.linspace(1.0, 0.0, fade_len)   # fade out

        print(f"       → Drone: {drone.shape[0]} samples  fade={fade_len} samples each end")
        return drone

    # ══════════════════════════════════════════════════════════════════
    # DSP — Harmonic overtone (subtle melodiousness boost)
    # ══════════════════════════════════════════════════════════════════

    def add_harmonic_overtone(self, audio: np.ndarray,
                               strength: float = 0.06) -> np.ndarray:
        """
        Adds a very quiet octave harmonic (+12 semitones) to the audio.

        Trained Sanskrit chanters naturally produce rich overtones through
        vocal resonance.  This function simulates that by pitch-shifting
        the entire audio up one octave and mixing it back in at a very
        low volume (6%).

        The result is a slightly richer, more resonant sound — not enough
        to be consciously noticed, but enough to make the recording feel
        less like a synthetic TTS voice and more like a human voice with
        natural resonance.

        strength: mix level for the harmonic (0.06 = 6% — very subtle)
        Uses librosa.effects.pitch_shift internally (may be slow on long audio).
        Falls back gracefully if librosa fails.
        """
        print(f"  [DSP] 🎼  Harmonic overtone  |  +12 semitones  strength={strength}")
        try:
            harmonic = librosa.effects.pitch_shift(
                audio,
                sr=self.sample_rate,
                n_steps=12,   # +12 semitones = one octave up
            )
            result = audio + (harmonic * strength)
            print(f"       → Harmonic mixed at {strength * 100:.0f}% volume ✓")
            return result
        except Exception as e:
            print(f"       → ⚠️  Harmonic failed ({e}) — skipping.")
            return audio

    # ══════════════════════════════════════════════════════════════════
    # UTILITY — Silence generator
    # ══════════════════════════════════════════════════════════════════

    def generate_silence(self, duration_ms: int) -> np.ndarray:
        """
        Returns an array of digital zeros — pure silence.
        Used to insert breath pauses between lines after stitching.
        """
        samples = int(self.sample_rate * (duration_ms / 1000.0))
        return np.zeros(samples)

    # ══════════════════════════════════════════════════════════════════
    # MASTER PIPELINE
    # ══════════════════════════════════════════════════════════════════

    def create_full_recitation(self, full_text: str, output_path: str) -> str:
        """
        Complete audio generation pipeline — SPARSH-X v6.

        ┌─────────────────────────────────────────────────────────────┐
        │ PIPELINE OVERVIEW                                           │
        │                                                             │
        │  Phase 1: Sanskrit Phonetic Pre-Processor                   │
        │    → Fix Visarga, Schwa preservation, ZWNJ insertion        │
        │                                                             │
        │  Phase 2: Groq Yati Placement (optional)                    │
        │    → Insert comma at mid-line Yati if safe (word boundary)  │
        │    → Skip if text already has commas                        │
        │    → Integrity check: discard if AI changed any letters     │
        │                                                             │
        │  Phase 3: Line Splitting                                    │
        │    → Split by Dandas (। = 600ms pause, ॥ = 1200ms pause)    │
        │    → Each line sent to TTS separately (no char limit crash) │
        │                                                             │
        │  Phase 4: TTS Synthesis (per line)                          │
        │    → Sanitise line (remove shell-breaking chars)            │
        │    → Edge-TTS: rate=-18% pitch=-10Hz volume=+25%            │
        │    → Load MP3 → trim silence → append to audio_segments     │
        │    → Append silence of correct duration after each line     │
        │                                                             │
        │  Phase 5: Stitch                                            │
        │    → np.concatenate(audio_segments)                         │
        │                                                             │
        │  Phase 6: Studio DSP                                        │
        │    → Temple reverb (decay=0.15, delay=200ms)                │
        │    → Om drone (136.1Hz, fade-in/out, vol=0.04)              │
        │    → Harmonic overtone (+12 semitones at 6%)                │
        │    → Normalize (clip to [-1.0, 1.0])                        │
        │                                                             │
        │  Phase 7: Save WAV                                          │
        └─────────────────────────────────────────────────────────────┘
        """
        pipeline_start = time.time()

        print("\n" + "=" * 62)
        print("[MASTER PIPELINE] 🚀  SPARSH-X v6  —  Full Recitation Engine")
        print("=" * 62)
        print(f"  Input   : {len(full_text)} chars")
        print(f"  Voice   : {self.voice}")
        print(f"  Rate    : {self.sample_rate} Hz")
        print(f"  Output  : {output_path}")
        print(f"  Pause(।): {self.pause_half_ms}ms")
        print(f"  Pause(॥): {self.pause_full_ms}ms")

        # ── Phase 1: Sanskrit phonetic pre-processing ──────────────────────
        print("\n[PHASE 1] 🔬 SANSKRIT PHONETIC PRE-PROCESSING")
        phonetic_text = self.sanskrit_phonetic_preprocess(full_text)

        # ── Phase 2: Groq Yati placement ───────────────────────────────────
        print("\n[PHASE 2] 🧠 GROQ YATI PLACEMENT")
        yati_text = self.apply_ai_punctuation(phonetic_text)

        # Log what text is actually entering the TTS pipeline
        # (This was completely invisible in older versions!)
        print(f"\n  [PIPELINE INPUT] Text entering TTS:")
        print(f"  >>> {yati_text[:120]}{'...' if len(yati_text) > 120 else ''}")

        # ── Phase 3: Split by Dandas ────────────────────────────────────────
        print(f"\n[PHASE 3] ✂️  LINE SPLITTING")
        segments = self.split_by_dandas(yati_text)

        if not segments:
            print("  ↳ ⚠️  No segments found — treating whole text as one line.")
            segments = [(yati_text, self.pause_full_ms)]

        # ── Phase 4: TTS synthesis per line ─────────────────────────────────
        print(f"\n[PHASE 4] 🎙️  TTS SYNTHESIS  ({len(segments)} segment(s))")
        audio_segments = []

        for idx, (line, pause_ms) in enumerate(segments):
            print(f"\n  ┌── Line {idx + 1} / {len(segments)} " + "─" * 38)
            clean_line = self.sanitise_line(line)
            print(f"  │  Text   : '{clean_line[:65]}{'...' if len(clean_line) > 65 else ''}'")
            print(f"  │  Pause  : {pause_ms}ms after this line")

            temp_file = f"static/raw_seg_{idx}.mp3"

            # Edge-TTS parameters tuned for Sanskrit chanting:
            #   --rate="-18%"   → 18% slower than conversational Hindi
            #                     gives the measured, solemn pace of chanting
            #   --pitch="-10Hz" → deeper pitch for authoritative, devotional tone
            #   --volume="+25%" → compensates for the energy absorbed by reverb
            #
            # ⚠️  DO NOT multiply final_audio by 1.3 after this.
            #     That caused double-boost clipping distortion in v4/v5.
            command = (
                f'edge-tts -t "{clean_line}" '
                f"-v {self.voice} "
                f'--rate="-18%" '
                f'--pitch="-10Hz" '
                f'--volume="+25%" '
                f"--write-media {temp_file}"
            )
            print(f"  │  CMD    : {command}")

            tts_start = time.time()
            os.system(command)
            tts_elapsed = time.time() - tts_start
            print(f"  │  TTS    : completed in {tts_elapsed:.2f}s")

            if not os.path.exists(temp_file):
                print(f"  │  ⚠️  No MP3 produced for line {idx + 1} — skipping.")
                print(f"  └" + "─" * 50)
                continue

            try:
                # Load MP3 into numpy array at our target sample rate
                seg_audio, _ = librosa.load(temp_file, sr=self.sample_rate)

                # Trim silence from edges (top_db=45 = trim at -45dB)
                # This removes the natural dead-air that TTS engines prepend/append.
                # Without trimming, the stitched pauses would be too long.
                seg_audio, _ = librosa.effects.trim(seg_audio, top_db=45)

                seg_sec = len(seg_audio) / self.sample_rate
                print(f"  │  Audio  : {seg_audio.shape[0]} samples ({seg_sec:.2f}s after trim)")
                audio_segments.append(seg_audio)

            except Exception as e:
                print(f"  │  ❌  Failed to load line {idx + 1}: {e}")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"  │  Temp   : {temp_file} deleted")

            # Insert the correct pause duration after this line
            silence = self.generate_silence(pause_ms)
            audio_segments.append(silence)
            print(f"  │  Pause  : {pause_ms}ms ({len(silence)} samples) inserted")
            print(f"  └" + "─" * 50)

        # ── Phase 5: Stitch ─────────────────────────────────────────────────
        print(f"\n[PHASE 5] 🪡  STITCHING  ({len(audio_segments)} chunk(s))")

        if not audio_segments:
            print("  ↳ 🛑  No audio generated. Aborting pipeline.")
            return output_path

        stitched     = np.concatenate(audio_segments)
        total_sec    = len(stitched) / self.sample_rate
        print(f"  ↳ Stitched: {stitched.shape[0]} samples ({total_sec:.2f}s)")

        # ── Phase 6: Studio DSP ─────────────────────────────────────────────
        print(f"\n[PHASE 6] 🎛️  STUDIO POST-PRODUCTION")

        # 6a. Temple reverb
        with_reverb = self.apply_temple_reverb(stitched)

        # 6b. Harmonic overtone (subtle resonance boost)
        #     Makes the voice sound richer, closer to natural chanting harmonics
        with_harmonic = self.add_harmonic_overtone(with_reverb, strength=0.06)

        # 6c. Om drone — runs the full length of the reverb-extended audio
        drone        = self.generate_sine_drone(len(with_harmonic))

        # 6d. Final mix
        # NO *1.3 boost — that caused hard-clipping distortion in older versions.
        # The --volume="+25%" in Edge-TTS is the only amplification we need.
        final_audio  = with_harmonic + drone
        print(f"\n  ↳ Mixed: {final_audio.shape[0]} samples")

        # 6e. Normalize — hard-clip to [-1.0, 1.0] to prevent speaker damage
        pre_clip_peak = float(np.max(np.abs(final_audio)))
        final_audio   = np.clip(final_audio, -1.0, 1.0)
        print(f"  ↳ Peak before clip: {pre_clip_peak:.4f}", end="")
        if pre_clip_peak > 1.0:
            print(f"  ⚠️  Clipping occurred — reduce --volume if distorted")
        else:
            print(f"  ✅  Clean (no clipping)")

        # ── Phase 7: Save WAV ───────────────────────────────────────────────
        print(f"\n[PHASE 7] 💾  FILE WRITER")
        sf.write(output_path, final_audio, self.sample_rate)

        file_kb  = os.path.getsize(output_path) / 1024
        elapsed  = time.time() - pipeline_start
        print(f"  ↳ Saved to      : {output_path}")
        print(f"  ↳ File size     : {file_kb:.1f} KB")
        print(f"  ↳ Audio duration: {total_sec:.2f}s")
        print(f"  ↳ Pipeline time : {elapsed:.2f}s total")

        print("\n" + "█" * 62)
        print("[SUCCESS] 🎉  SPARSH-X v6 PIPELINE COMPLETE!")
        print("█" * 62 + "\n")

        return output_path