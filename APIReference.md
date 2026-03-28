# ChandasAI — API Reference

Complete backend API reference for ChandasAI. The server is powered by **FastAPI** and runs the SPARSH-X analysis and audio pipeline.

← Back to [README.md](./README.md)

---

## 🌐 Base URL

```
http://127.0.0.1:8000
```

---

## 📋 Endpoints Overview

| Method |     Endpoint      |                     Description                     |
|--------|-------------------|-----------------------------------------------------|
| `POST` | `/analyze-text`   | Analyse a verse — metre, laghu-guru, syllable count |
| `POST` | `/generate-audio` | Generate a Sanskrit recitation WAV file             |
| `GET`  | `/audio`          | Stream the generated WAV to the browser             |

---

## 📐 Endpoint 1 — Analyze Verse

Analyzes a Sanskrit verse and returns its metre, per-syllable Laghu/Guru classification, and the raw pattern string. Automatically converts ITRANS / English input to Devanagari before processing.

**Method & Path**
```
POST /analyze-text
```

**Request Body (JSON)**
```json
{
  "text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | String | ✅ Yes | Sanskrit verse in Devanagari or ITRANS transliteration |

**Success Response — `200 OK`**
```json
{
  "syllables": [
    { "text": "कर्",  "type": "G" },
    { "text": "म",    "type": "G" },
    { "text": "ण्ये", "type": "G" },
    { "text": "वा",   "type": "G" },
    { "text": "धि",   "type": "L" }
  ],
  "metre": "Anuṣṭubh",
  "raw_sequence": "GGGGL..."
}
```

| Field | Type | Description |
|---|---|---|
| `syllables` | Array | Each syllable with its text and `L` (Laghu) or `G` (Guru) weight |
| `metre` | String | Detected Sanskrit metre name. Groq AI fallback used if local DB has no match. |
| `raw_sequence` | String | Continuous Laghu-Guru string for the full verse (e.g. `GGGGLGGG...`) |

---

## 🎙️ Endpoint 2 — Generate Audio Recitation

Runs the verse through the full **SPARSH-X pipeline**: Groq AI adds Yati (half-breath) pauses, Edge-TTS synthesizes each line using Marathi Neural Voice, lines are stitched with correct pause lengths, and temple reverb with an Om drone is applied.

Returns the audio URL and 80 amplitude peaks for the frontend waveform bar chart.

**Method & Path**
```
POST /generate-audio
```

**Request Body (JSON)**
```json
{
  "text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | String | ✅ Yes | Sanskrit verse in Devanagari or ITRANS transliteration |

**Success Response — `200 OK`**
```json
{
  "audio_url": "http://127.0.0.1:8000/audio?t=1710500000",
  "waveform": [0.0, 12.5, 45.2, 88.9, 100.0, 32.1]
}
```

| Field | Type | Description |
|---|---|---|
| `audio_url` | String | URL to stream the generated WAV. Includes a Unix timestamp for browser cache-busting. |
| `waveform` | Array[float] | Exactly **80** normalized amplitude values between `0.0` and `100.0` for React bar chart rendering |

---

## 🎧 Endpoint 3 — Fetch Audio Stream

Streams the compiled `.wav` recitation file to the browser. Always call `/generate-audio` first — this endpoint only serves whatever file was last generated.

**Method & Path**
```
GET /audio
```

**Query Parameters**

| Parameter |   Type  | Required |                                Description                               |
|-----------|---------|----------|--------------------------------------------------------------------------|
| `t`       | Integer | No       | Unix timestamp appended by the frontend purely for browser cache-busting |

**Success Response — `200 OK`**
- `Content-Type: audio/wav`
- Body: Binary WAV audio stream
- Includes `Cache-Control: no-store` headers to prevent stale playback

**Error Response — `404 Not Found`**
```json
{
  "detail": "Audio file not found."
}
```

---

## 💡 Example — Full Integration Flow

A complete request/response cycle from verse input to audio playback:

**Step 1 — Analyze the verse**
```bash
curl -X POST http://127.0.0.1:8000/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।"}'
```

**Step 2 — Generate the recitation audio**
```bash
curl -X POST http://127.0.0.1:8000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।"}'
```

**Step 3 — Stream the audio**
```bash
curl http://127.0.0.1:8000/audio --output recitation.wav
```

---

## ⚙️ Configuration Notes

- Requires `GROQ_API_KEY` set in `backend/.env` for AI metre fallback and Yati insertion
- Audio is generated using **Marathi Neural Voice** (`mr-IN-AarohiNeural`) to preserve Sanskrit vowel endings
- If ITRANS / English input is detected, the engine auto-converts to Devanagari before any analysis
- The Groq fallback uses `llama-3.3-70b-versatile` with a full metre lookup table (Gāyatrī through Sragdharā) for accurate identification when the local database has no match

---

## 🚧 Known Limitations

- Audio generation requires an active internet connection for Edge-TTS synthesis
- Very long verses (4+ ślokas) may increase audio generation time significantly
- Metre detection accuracy depends on correct Devanagari Unicode input — see [Troubleshooting](./README.md#️-common-input-mistakes--troubleshooting) in the README

---

## 👨‍💻 Author

**Swayam Rudraxi**
