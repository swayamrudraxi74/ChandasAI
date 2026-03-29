# ==========================================
# engine/recitation_helper.py  —  SPARSH-X Audio Engine v7
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
        print("[SYSTEM INIT] 🛠️  SPARSH-X Audio Engine  v7")
        print(f"[SYSTEM INIT] 🎛️  Sample rate    : {sample_rate} Hz (CD quality)")
        print("█" * 62 + "\n")

        self.sample_rate = sample_rate

        # Microsoft Hindi Neural voice — best Schwa retention for Sanskrit
        self.voice = "hi-IN-SwaraNeural"

        # Pause durations
        self.pause_half_ms = 800
        self.pause_full_ms = 1500

        # Groq client — kept for metre detection in app.py ONLY.
        # Phase 1 and Phase 2 of recitation_helper no longer use it.
        self.groq_client = None
        try:
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("[SYSTEM INIT] 🟢  Groq API authenticated (metre fallback only).")
        except Exception as e:
            print(f"[SYSTEM INIT] 🔴  Groq unavailable: {e}")

    # ══════════════════════════════════════════════════════════════════
    # STRICT MATH ENGINE — Sanskrit Prosody (Chandas)
    # (UNCHANGED from v6 — this was already correct)
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
                continue

            if curr["is_halant"]:
                if len(final_aksharas) > 0:
                    final_aksharas[-1]["text"] += curr["text"]
                    final_aksharas[-1]["lg"] = "G"
                continue

            next_syl = None
            for k in range(j + 1, len(akshara_list)):
                if not akshara_list[k]["is_space"]:
                    next_syl = akshara_list[k]
                    break

            if next_syl:
                if next_syl["consonant_count"] > 1:
                    curr["lg"] = "G"
                if next_syl["is_halant"]:
                    curr["lg"] = "G"

            final_aksharas.append(curr)

        return final_aksharas

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1 — SANSKRIT PHONETIC PRE-PROCESSOR (RULE-BASED, NO AI)
    # ══════════════════════════════════════════════════════════════════

    def sanskrit_phonetic_preprocess(self, text: str) -> str:
        """
        Deterministic, rule-based Sanskrit phonetic pre-processor.

        WHY NO AI:
          Groq (LLM) was instructed to "append अ to consonants" which caused:
            → "सर्वे" became "सर्वे-अ"  (phantom vowel on a vowel-ending syllable)
            → "सङ्गोऽस्त्व" became "Sangotsav" (hallucinated nearest Marathi word)
          LLMs CANNOT reliably manipulate Devanagari at the character level.
          A deterministic rule-based system is always correct.

        WHY NO ZWNJ (\u200c):
          Inserting ZWNJ after a virama (e.g. ण्‌य) isolates the dead consonant.
          The TTS engine panics on isolated dead consonants (no vowel attached)
          and inserts phantom "i" or "u" vowels → "Karman-iy-eva".
          The TTS handles ण्य correctly on its own when the AI is NOT mangling
          the text first.

        RULES APPLIED (two rules only — nothing else):

          Rule 1 — Avagraha (ऽ):
            Remove entirely. The Hindi TTS has no understanding of the
            Sanskrit Avagraha symbol and generates noise or hallucinations
            when it encounters one. Removing it exposes the underlying
            Sandhi cluster (e.g. स्त्व) which the TTS reads correctly.

          Rule 2 — Visarga (ः):
            Context-aware two-pass replacement:
            Pass A: ः immediately before a Devanagari consonant → ह्
                    Correct phonetics: दुःख → दुह्ख → TTS says "duh-kha" ✓
            Pass B: ः before space / comma / danda / end-of-string → ह
                    Correct phonetics: सुखिनः → सुखिनह → TTS says "sukhina-h" ✓
            Pass C: Any remaining ः → ह  (safety net)
        """
        print("\n  [PHONETICS] 🔬 Rule-based pre-processor (v7, no AI)...")
        original_len = len(text)

        # All Devanagari consonants (Unicode range 0x0915–0x0939)
        # Used in regex character classes below.
        CONSONANTS = "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"

        # ── Rule 1: Avagraha (ऽ, U+093D) → remove ─────────────────────
        # "सङ्गोऽस्त्वकर्मणि" → "सङ्गोस्त्वकर्मणि"
        # Without Avagraha, TTS reads the cluster normally.
        text = text.replace("\u093D", "")   # ऽ
        text = text.replace("ऽ", "")        # belt-and-suspenders (literal char)

        # ── Rule 2: Visarga (ः, U+0903) context-aware replacement ─────
        # Pass A: ः before a consonant → ह् (half-h, no trailing vowel)
        text = re.sub(f"\u0903([{CONSONANTS}])", r"ह्\1", text)
        # Pass B: ः before space / comma / danda / end-of-string → ह
        text = re.sub(r"\u0903(?=[\s,।॥]|$)", "ह", text)
        # Pass C: any remaining ः → ह  (safety net)
        text = text.replace("\u0903", "ह")

        print(f"  [PHONETICS] ✅ Done ({original_len} → {len(text)} chars).")
        print(f"  ↳ Result: '{text[:80]}{'...' if len(text) > 80 else ''}'")
        return text

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2 — MATHEMATICAL YATI PLACEMENT (NO AI)
    # ══════════════════════════════════════════════════════════════════

    def apply_ai_punctuation(self, text: str) -> str:
        """
        Inserts Yati (mid-line breath pause) commas using syllable mathematics.

        WHY NO AI:
          The previous Groq-based Yati placer computed len(text)//2 and
          inserted ONE comma at that character position, regardless of
          syllable boundaries.  For Anushtubh (8 syllables/pāda), the Yati
          falls after the 4th syllable — which is almost never at the
          character midpoint.

        ALGORITHM:
          1. If commas already exist in text → skip (user has manual Yati).
          2. Split text by dandas (। ॥) and newlines → individual pādas.
          3. For each pāda, split into words and count syllables per word
             using syllabify_pada() (the same strict Chandas engine).
          4. Walk through words accumulating syllable counts until we cross
             half the pāda's total syllables.
          5. Insert a comma after that word.
          6. Skip pādas with ≤ 3 total syllables (too short to need Yati).

        WHY WORD BOUNDARIES:
          Inserting a comma in the middle of a Sanskrit compound word causes
          the TTS to mispronounce it.  We always place Yati at a word gap.
        """
        if "," in text:
            print("\n  [YATI] ⏩ Commas already present — skipping (manual Yati).")
            return text

        print("\n  [YATI] 📐 Mathematical Yati placement (v7, no AI)...")
        print(f"  ↳ Input : '{text[:70]}{'...' if len(text) > 70 else ''}'")

        # Split on dandas and newlines, keeping the delimiters in the list
        # so we can reconstruct the string faithfully after processing.
        parts = re.split(r"(।|॥|\n)", text)

        result = []
        for part in parts:
            # Delimiters and empty strings pass through unchanged
            if part in ("।", "॥", "\n", ""):
                result.append(part)
                continue

            stripped = part.strip()
            if not stripped:
                result.append(part)
                continue

            # Apply Yati to this pāda segment
            yati_segment = self._insert_yati_into_pada(stripped)

            # Preserve any leading/trailing whitespace that was in `part`
            result.append(part.replace(stripped, yati_segment, 1))

        yati_text = "".join(result)
        print(f"  [YATI] ✅ Yati applied.")
        print(f"  ↳ Result: '{yati_text[:80]}{'...' if len(yati_text) > 80 else ''}'")
        return yati_text

    def _insert_yati_into_pada(self, pada_text: str) -> str:
        """
        Insert a single Yati comma into one pāda at the correct syllable boundary.

        Finds the word boundary whose cumulative syllable count is closest
        to half the total syllable count of the pāda.

        Example (Anushtubh, 8 syllables, Yati after syllable 4):
          "सर्वे भवन्तु सुखिनह" → syllables: [2, 3, 3] → total=8, target=4
          After word 1 (सर्वे) : cumulative=2
          After word 2 (भवन्तु): cumulative=5  ← first to cross target=4
          → comma after word 2 → "सर्वे भवन्तु, सुखिनह"

        Returns pada_text unchanged if:
          - Only one word (no word boundary to split at)
          - Total syllables < 4 (too short to benefit from Yati)
        """
        words = pada_text.split()
        if len(words) <= 1:
            return pada_text

        # Count syllables in each word (strip stray punctuation first)
        word_syl_counts = []
        for word in words:
            clean = re.sub(r"[,।॥।]", "", word).strip()
            if clean:
                try:
                    aksharas = self.syllabify_pada(clean)
                    word_syl_counts.append(len(aksharas))
                except Exception:
                    word_syl_counts.append(1)   # fallback: treat as 1 syllable
            else:
                word_syl_counts.append(0)

        total = sum(word_syl_counts)
        if total < 4:
            return pada_text    # pāda too short for Yati

        target = total / 2.0   # Yati ideally at midpoint syllable

        # Walk left-to-right; split after the first word that pushes us
        # to or past the syllable midpoint.
        cumulative  = 0
        best_split  = 1        # default: after the first word (safety)

        # Never split after the LAST word (nothing would come after the comma)
        for i in range(len(word_syl_counts) - 1):
            cumulative += word_syl_counts[i]
            if cumulative >= target:
                best_split = i + 1
                break

        before = " ".join(words[:best_split])
        after  = " ".join(words[best_split:])

        if after:
            return before + ", " + after
        return pada_text

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3 — LINE SPLITTER: respects Danda verse structure
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def split_by_dandas(self, text: str) -> list:
        """
        Splits the Sanskrit verse into (line_text, pause_ms) pairs.

        WHY SPLIT AT ALL?
          Edge-TTS silently stops after ~200–250 chars in a single request.
          Line-by-line generation eliminates this problem.

        PAUSE LENGTHS:
          ।  (single Danda) = half-verse boundary → 800ms
          ॥  (double Danda) = full-verse boundary → 1500ms
          \\n (newline)      = treated as single Danda → 800ms
        """
        print("\n  [SPLIT] ✂️  Splitting by Danda boundaries...")
        print(f"  ↳ Input : {len(text)} characters")

        normalised    = text.replace("\n", "।")
        segments      = []
        current_chunk = ""

        for ch in normalised:
            if ch == "॥":
                if current_chunk.strip():
                    segments.append((current_chunk.strip(), self.pause_full_ms))
                current_chunk = ""
            elif ch == "।":
                if current_chunk.strip():
                    segments.append((current_chunk.strip(), self.pause_half_ms))
                current_chunk = ""
            else:
                current_chunk += ch

        if current_chunk.strip():
            segments.append((current_chunk.strip(), self.pause_full_ms))

        print(f"  ↳ Found {len(segments)} segment(s):\n")
        for idx, (seg, pause) in enumerate(segments):
            preview = seg[:50] + ("..." if len(seg) > 50 else "")
            print(f"     [{idx + 1}] '{preview}'  → pause={pause}ms")

        return segments

    # ══════════════════════════════════════════════════════════════════
    # PHASE 4 — TTS LINE SANITISER
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def sanitise_line(self, text: str) -> str:
        """
        Final cleanup before sending a line to Edge-TTS.
        Removes double-quotes (break shell command) and stray newlines.
        Does NOT touch Devanagari letters — phonetics are done in Phase 1.
        """
        text = text.replace('"', "")
        text = text.replace("\n", " ").replace("\r", " ")
        return text.strip()

    # ══════════════════════════════════════════════════════════════════
    # DSP — Temple reverb
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def apply_temple_reverb(self, audio: np.ndarray,
                             delay_ms: int = 200,
                             decay: float = 0.15) -> np.ndarray:
        """
        Adds an acoustic echo simulating a large stone temple hall.
        decay=0.15 keeps the echo subtle (v6 fix from 0.30).
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
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def generate_sine_drone(self, num_samples: int,
                             frequency: float = 136.1,
                             volume: float = 0.04) -> np.ndarray:
        """
        136.1 Hz = classical Om tuning (C#).  Sits below voice range.
        90ms fade-in/out prevents abrupt click (v6 fix).
        """
        print(f"  [DSP] 🧘  Om Drone  |  {frequency} Hz  vol={volume}")
        t     = np.linspace(0, num_samples / self.sample_rate,
                            num_samples, endpoint=False)
        drone = np.sin(2 * np.pi * frequency * t) * volume

        fade_len = min(4000, num_samples // 4)
        drone[:fade_len]  *= np.linspace(0.0, 1.0, fade_len)
        drone[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

        print(f"       → Drone: {drone.shape[0]} samples  fade={fade_len} samples each end")
        return drone

    # ══════════════════════════════════════════════════════════════════
    # DSP — Harmonic overtone (subtle melodiousness boost)
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def add_harmonic_overtone(self, audio: np.ndarray,
                               strength: float = 0.06) -> np.ndarray:
        """
        Adds a quiet octave harmonic (+12 semitones at 6%) to simulate
        the natural vocal resonance of trained Sanskrit chanters.
        Falls back gracefully if librosa fails.
        """
        print(f"  [DSP] 🎼  Harmonic overtone  |  +12 semitones  strength={strength}")
        try:
            harmonic = librosa.effects.pitch_shift(
                audio, sr=self.sample_rate, n_steps=12,
            )
            result = audio + (harmonic * strength)
            print(f"       → Harmonic mixed at {strength * 100:.0f}% volume ✓")
            return result
        except Exception as e:
            print(f"       → ⚠️  Harmonic failed ({e}) — skipping.")
            return audio

    # ══════════════════════════════════════════════════════════════════
    # UTILITY — Silence generator
    # (UNCHANGED from v6)
    # ══════════════════════════════════════════════════════════════════

    def generate_silence(self, duration_ms: int) -> np.ndarray:
        """Returns an array of zeros (pure silence) for breath pauses."""
        samples = int(self.sample_rate * (duration_ms / 1000.0))
        return np.zeros(samples)

    # ══════════════════════════════════════════════════════════════════
    # MASTER PIPELINE
    # (UNCHANGED from v6 — fixes were in Phase 1 & 2 above)
    # ══════════════════════════════════════════════════════════════════

    def create_full_recitation(self, full_text: str, output_path: str) -> str:
        """
        Complete audio generation pipeline — SPARSH-X v7.

        ┌─────────────────────────────────────────────────────────────┐
        │ PIPELINE OVERVIEW                                           │
        │                                                             │
        │  Phase 1: Sanskrit Phonetic Pre-Processor (RULE-BASED v7)  │
        │    → Remove Avagraha (ऽ)                                   │
        │    → Fix Visarga (ः) context-aware                         │
        │    → NO AI — zero hallucinations                           │
        │                                                             │
        │  Phase 2: Mathematical Yati Placement (NO AI, v7)          │
        │    → Count syllables using syllabify_pada()                │
        │    → Insert comma at word boundary nearest syllable mid    │
        │    → Skip if commas already present                        │
        │                                                             │
        │  Phase 3: Line Splitting                                    │
        │    → Split by Dandas (। = 800ms pause, ॥ = 1500ms pause)   │
        │    → Each line sent to TTS separately (no char limit crash) │
        │                                                             │
        │  Phase 4: TTS Synthesis (per line)                          │
        │    → Sanitise line (remove shell-breaking chars)            │
        │    → Edge-TTS: rate=-18% pitch=-10Hz volume=+25%           │
        │    → Load MP3 → trim silence → append to audio_segments    │
        │    → Append silence of correct duration after each line    │
        │                                                             │
        │  Phase 5: Stitch                                            │
        │    → np.concatenate(audio_segments)                        │
        │                                                             │
        │  Phase 6: Studio DSP                                        │
        │    → Temple reverb (decay=0.15, delay=200ms)               │
        │    → Harmonic overtone (+12 semitones at 6%)               │
        │    → Om drone (136.1Hz, fade-in/out, vol=0.04)             │
        │    → Normalize (clip to [-1.0, 1.0])                       │
        │                                                             │
        │  Phase 7: Save WAV                                          │
        └─────────────────────────────────────────────────────────────┘
        """
        pipeline_start = time.time()

        print("\n" + "=" * 62)
        print("[MASTER PIPELINE] 🚀  SPARSH-X v7  —  Full Recitation Engine")
        print("=" * 62)
        print(f"  Input   : {len(full_text)} chars")
        print(f"  Voice   : {self.voice}")
        print(f"  Rate    : {self.sample_rate} Hz")
        print(f"  Output  : {output_path}")
        print(f"  Pause(।): {self.pause_half_ms}ms")
        print(f"  Pause(॥): {self.pause_full_ms}ms")

        # ── Phase 1: Sanskrit phonetic pre-processing (rule-based) ────────
        print("\n[PHASE 1] 🔬 SANSKRIT PHONETIC PRE-PROCESSING (rule-based, no AI)")
        phonetic_text = self.sanskrit_phonetic_preprocess(full_text)

        # ── Phase 2: Mathematical Yati placement (no AI) ──────────────────
        print("\n[PHASE 2] 📐 MATHEMATICAL YATI PLACEMENT (no AI)")
        yati_text = self.apply_ai_punctuation(phonetic_text)

        # Log what text is actually entering the TTS pipeline
        print(f"\n  [PIPELINE INPUT] Text entering TTS (Phase 3+):")
        print(f"  >>> {yati_text[:140]}{'...' if len(yati_text) > 140 else ''}")

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
                seg_audio, _ = librosa.load(temp_file, sr=self.sample_rate)
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

            silence = self.generate_silence(pause_ms)
            audio_segments.append(silence)
            print(f"  │  Pause  : {pause_ms}ms ({len(silence)} samples) inserted")
            print(f"  └" + "─" * 50)

        # ── Phase 5: Stitch ─────────────────────────────────────────────────
        print(f"\n[PHASE 5] 🪡  STITCHING  ({len(audio_segments)} chunk(s))")

        if not audio_segments:
            print("  ↳ 🛑  No audio generated. Aborting pipeline.")
            return output_path

        stitched  = np.concatenate(audio_segments)
        total_sec = len(stitched) / self.sample_rate
        print(f"  ↳ Stitched: {stitched.shape[0]} samples ({total_sec:.2f}s)")

        # ── Phase 6: Studio DSP ─────────────────────────────────────────────
        print(f"\n[PHASE 6] 🎛️  STUDIO POST-PRODUCTION")

        with_reverb   = self.apply_temple_reverb(stitched)
        with_harmonic = self.add_harmonic_overtone(with_reverb, strength=0.06)
        drone         = self.generate_sine_drone(len(with_harmonic))
        final_audio   = with_harmonic + drone
        print(f"\n  ↳ Mixed: {final_audio.shape[0]} samples")

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

        file_kb = os.path.getsize(output_path) / 1024
        elapsed = time.time() - pipeline_start
        print(f"  ↳ Saved to      : {output_path}")
        print(f"  ↳ File size     : {file_kb:.1f} KB")
        print(f"  ↳ Audio duration: {total_sec:.2f}s")
        print(f"  ↳ Pipeline time : {elapsed:.2f}s total")

        print("\n" + "█" * 62)
        print("[SUCCESS] 🎉  SPARSH-X v7 PIPELINE COMPLETE!")
        print("█" * 62 + "\n")

        return output_path