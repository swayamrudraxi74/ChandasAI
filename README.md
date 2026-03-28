# ChandasAI

AI-powered Sanskrit prosody analyzer for metre detection, laghu-guru parsing, recitation assistance, and poetic structure verification.

---

## 📚 Documentation

|                 File                 |                              Description                               |
|--------------------------------------|------------------------------------------------------------------------|
| [README.md](./README.md)             | Project overview, setup guide, analysis rules, and examples            |
| [APIReference.md](./APIReference.md) | All backend endpoints, request/response schemas, and integration notes |

---

## Overview

ChandasAI is a Sanskrit computational analysis system designed to perform mathematically accurate metrical analysis of Sanskrit verses using classical Chandas rules and phonetic parsing.

It identifies:
- Chandas (metre)
- Laghu-Guru sequence
- Gana structure
- Syllable count
- Recitation guidance
- Pronunciation-sensitive parsing

---

## ✨ Core Features

- Accurate Laghu-Guru detection
- Automatic metre matching
- Sanskrit syllable parser
- Gana analysis engine
- Recitation helper
- Audio-assisted pronunciation
- Sandhi-aware parsing
- Devanagari input support
- Transliteration-aware logic

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI

### Frontend
- React
- TypeScript
- Vite

### Data Engine
- JSON-based Sanskrit rule datasets

---

## 🗂️ Project Structure

```text
ChandasAI/
│── backend/
│   ├── api/
│   ├── engine/
│   ├── data/
│   └── static/
│
│── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── hooks/
│
│── .gitignore
│── start_project.bat
│── README.md
│── APIReference.md
```

---

## 🚀 How to Run

### Backend
Navigate to the backend directory, install the dependencies, and run the API server:
```bash
cd backend
pip install -r requirements.txt
python api/app.py
```

### Frontend
Navigate to the frontend directory, install the Node modules, and start the development server:
```bash
cd frontend
npm install
npm run dev
```

> **Integrating with the API directly?** See the full [API Reference →](./APIReference.md)

---

## 📏 Core Analysis Rules

The engine strictly follows classical Sanskrit Chandas principles:
- Short vowels → **Laghu**
- Long vowels → **Guru**
- Anusvara (`ं`) makes the previous syllable **Guru**
- Visarga (`ः`) makes the previous syllable **Guru**
- Conjunct consonants (Samyuktakshara) convert the previous short syllable into **Guru**
- Pada endings are handled according to metrical rules
- Sandhi is preserved mathematically

---

## ⚠️ Common Input Mistakes & Troubleshooting

To get mathematically perfect syllable counts (Guru/Laghu) and flawless audio recitation, your input text must be highly accurate.

### 1. Visarga (ः) and Anusvara (ं) Misplacement
- **Example:** `सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः।`
- **Mistake:** Using a standard English colon (`:`) instead of a true Visarga (`ः`), or incorrect nasal symbols.
- **Fix:** Always use true Devanagari characters. The engine relies on them to calculate heavy (Guru) syllables perfectly.

### 2. Avagraha (ऽ) Phantom Syllable
- **Example:** `मा ते सङ्गोऽस्त्वकर्मणि॥`
- **Mistake:** The Avagraha may falsely increase the syllable count if treated as a full physical character, ruining metre detection.
- **Fix:** The SPARSH-X engine automatically ignores the Avagraha mathematically, but you must ensure you use the correct Unicode symbol (`\u093D`), not an English 'S' or a number '5'.

### 3. Sandhi Compound TTS Difficulty
- **Example:** `या शुभ्रवस्त्रावृता`
- **Mistake:** Long Sandhi compounds may distort the Text-to-Speech (TTS) output or cause the voice to rush.
- **Better Input:** `या कुन्देन्दु तुषार हार धवला` — adding spaces improves recitation flow while perfectly preserving the mathematical analysis.

### 4. Conjunct Consonant Illusion
- **Example:** `कर्मण्येवाधिकारस्ते`
- **Mistake:** Simple visual counters or standard LLMs miscount short vowels before conjunct consonants as Laghu.
- **Fix:** The SPARSH-X engine correctly looks ahead and applies the conjunct Guru rule automatically (e.g., recognizing `क` as Guru because `र्म` follows it). Trust the engine's numbers!

### 5. Hindi "Schwa Deletion" Problem
- **Example:** `राम` / `तुषार`
- **Mistake:** Standard Hindi voices remove the final short 'a', pronouncing them as "Rām" and "Tushār", which destroys the metre.
- **Fix:** The recitation logic natively uses Marathi Neural Voices (`mr-IN-AarohiNeural` or `mr-IN-ManoharNeural`) to ensure Sanskrit vowel endings are spoken correctly out of the box.

---

## 🚧 Known Development Challenges

- Visarga normalization errors
- Avagraha overcounting in early builds *(Resolved in v6)*
- Sandhi-induced TTS instability
- Meter alias corrections
- Devanagari phonetic refinement

---

## 💡 Example Analysis

**Input Verse:**
```text
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥
```

**Engine Output:**
- **Meter:** Anuṣṭubh (अनुष्टुभ्)
- **Syllable Count:** 32 (8 per Pāda)
- **Total Guru (Heavy):** 20
- **Total Laghu (Light):** 12
- **Mathematical Breakdown:**
  - Pāda 1: `कर्(G) म(G) ण्ये(G) वा(G) धि(L) का(G) र(G) स्ते(G)`
  - Pāda 2: `मा(G) फ(L) ले(G) षु(L) क(L) दा(G) च(L) न(L)`
  - Pāda 3: `मा(G) क(G) र्म(L) फ(L) ल(L) हे(G) तु(G) र्भू(G)`
  - Pāda 4: `र्मा(G) ते(G) स(G) ङ्गो(G) स्त्व(L) क(G) र्म(L) णि(L)`

*(Note: The engine correctly upgrades short vowels to Guru when followed by conjuncts, outperforming standard generative AI models.)*

---

## 📊 Repository Status

- **Active development**
- Core engine functional
- Frontend integrated
- Dataset expandable

---

## 🎯 Possible Use Cases

- Sanskrit education
- Chandas verification
- Verse recitation practice
- Research assistance
- Computational linguistics

---

## 🔮 Future Improvements

- Expanded metre database
- Advanced recitation pitch analysis
- Batch verse analysis
- Enhanced transliteration interface

---

## 🤝 Contribution

Contributions, corrections, and metre dataset improvements are highly welcome. Feel free to open an issue or submit a pull request!

---

## 📄 License

Currently intended for educational and research purposes.

---

## 👨‍💻 Author

**Swayam Rudraxi**
