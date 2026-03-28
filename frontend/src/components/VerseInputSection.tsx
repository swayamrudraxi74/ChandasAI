import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ClipboardPaste, ChevronRight } from "lucide-react";

// Sample verses for quick testing
const SAMPLE_VERSES = [
  {
    label: "Bhagavad Gita 2.47",
    text: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥",
    transliteration: "karmaṇy-evādhikāras te mā phaleṣu kadācana",
  },
  {
    label: "Rig Veda 1.1.1",
    text: "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् ।\nहोतारं रत्नधातमम् ॥",
    transliteration: "agnim-īḷe purohitaṁ yajñasya devam-ṛtvijam",
  },
];

// Data structure definitions
type SyllableResult = { text: string; type: "L" | "G" };

interface VerseInputProps {
  onAnalysisComplete: (result: { syllables: SyllableResult[]; metre: string; verse: string }) => void;
}

export default function VerseInputSection({ onAnalysisComplete }: VerseInputProps) {
  // UI State tracking
  const [verse, setVerse] = useState("");
  const [analysing, setAnalysing] = useState(false);
  const [result, setResult] = useState<{ syllables: SyllableResult[]; metre: string } | null>(null);
  const [showSampleMenu, setShowSampleMenu] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const maxChars = 5000;

  // ==========================================
  // API CONNECTION TO PYTHON BACKEND
  // ==========================================
  const handleAnalyze = async () => {
    if (!verse.trim()) return;
    
    setAnalysing(true); // Spin the button
    
    try {
      const response = await fetch("http://127.0.0.1:8000/analyze-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: verse }), 
      });

      if (!response.ok) throw new Error("Backend connection failed");
      
      const data = await response.json();
      
      // Update local UI state to show the result boxes
      const res = { syllables: data.syllables, metre: data.metre };
      setResult(res); 
      
      // Push data up to Home.tsx so the Melody graph can use it
      onAnalysisComplete({ ...res, verse });
      
    } catch (error) {
      console.error(error);
      alert("Analysis failed! Make sure your Python backend (uvicorn) is running.");
    } finally {
      setAnalysing(false);
    }
  };

  const pasteSample = (sample: typeof SAMPLE_VERSES[0]) => {
    setVerse(sample.text);
    setShowSampleMenu(false);
    setResult(null); 
    textareaRef.current?.focus();
  };

  return (
    <section id="input" className="py-24 px-6 relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] dark:bg-indigo-600/6 bg-amber-200/20 blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full dark:bg-amber-500/10 bg-amber-100 dark:border border dark:border-amber-500/20 border-amber-300/40 mb-4">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-xs font-semibold tracking-widest uppercase dark:text-amber-400 text-amber-700">
              Step 1: Input
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold dark:text-white text-gray-900 mb-4">
            Enter a Sanskrit Verse
          </h2>
          <p className="dark:text-gray-400 text-gray-500 max-w-lg mx-auto">
            Paste any Sanskrit verse or śloka. Our engine will detect its metrical structure and classify each syllable.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="relative"
        >
          <div className="rounded-3xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-white/8 border-black/6 p-6 shadow-lg">
            
            {/* Input Box */}
            <div className="relative mb-4">
              <textarea
                ref={textareaRef}
                value={verse}
                onChange={(e) => { setVerse(e.target.value.slice(0, maxChars)); setResult(null); }}
                placeholder="धर्मक्षेत्रे कुरुक्षेत्रे..."
                rows={5}
                className="w-full rounded-2xl dark:bg-white/4 bg-black/3 dark:border border dark:border-white/10 border-black/8 px-5 py-4 text-lg dark:text-gray-100 text-gray-800 placeholder:dark:text-gray-600 placeholder:text-gray-300 resize-none focus:outline-none dark:focus:border-amber-500/50 focus:border-amber-400/50 focus:ring-2 dark:focus:ring-amber-500/10 focus:ring-amber-400/10 transition-all duration-300 font-serif leading-relaxed"
                style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
              />
              <div className="absolute bottom-3 right-4 text-xs dark:text-gray-600 text-gray-400">
                {verse.length}/{maxChars}
              </div>
            </div>

            {/* Controls */}
            <div className="flex flex-wrap gap-3 items-center justify-between">
              <div className="relative">
                <button
                  onClick={() => setShowSampleMenu(!showSampleMenu)}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl dark:bg-white/5 bg-black/5 dark:hover:bg-white/10 hover:bg-black/8 dark:border border dark:border-white/10 border-black/8 text-sm dark:text-gray-300 text-gray-600 font-medium transition-all duration-200"
                >
                  <ClipboardPaste className="w-4 h-4" />
                  Paste Sample Verse
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${showSampleMenu ? "rotate-90" : ""}`} />
                </button>

                <AnimatePresence>
                  {showSampleMenu && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.95 }}
                      transition={{ duration: 0.15 }}
                      className="absolute top-full left-0 mt-2 w-72 rounded-2xl dark:bg-[rgba(15,20,45,0.95)] bg-white border dark:border-white/10 border-black/8 shadow-2xl z-20 overflow-hidden"
                    >
                      {SAMPLE_VERSES.map((s) => (
                        <button
                          key={s.label}
                          onClick={() => pasteSample(s)}
                          className="w-full px-4 py-3 text-left dark:hover:bg-white/5 hover:bg-black/4 transition-colors"
                        >
                          <div className="text-sm font-semibold dark:text-amber-400 text-amber-600 mb-0.5">{s.label}</div>
                          <div className="text-xs dark:text-gray-500 text-gray-400 truncate">{s.transliteration}</div>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Action Button */}
              <motion.button
                whileHover={{ scale: 1.03, boxShadow: "0 0 28px rgba(245,158,11,0.35)" }}
                whileTap={{ scale: 0.97 }}
                onClick={handleAnalyze}
                disabled={!verse.trim() || analysing}
                className="flex items-center gap-2.5 px-7 py-3 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold text-sm shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
              >
                {analysing ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    />
                    {/* Changed text slightly to imply AI might be thinking */}
                    AI is processing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Detect Chandas & Melody
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* RESULTS RENDER BLOCK */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="mt-8"
            >
              {/* Metre Header */}
              <div className="rounded-2xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-amber-500/20 border-amber-300/30 p-6 mb-6 shadow-md">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-xs font-semibold uppercase tracking-widest dark:text-amber-400 text-amber-600">Detected Metre</span>
                </div>
                {/* This will now display the Groq output if it was triggered! */}
                <div className="text-3xl font-bold dark:text-white text-gray-900">{result.metre}</div>
                <div className="text-sm dark:text-gray-400 text-gray-500 mt-1">
                  {result.syllables.length} syllables analyzed · {result.syllables.filter(s => s.type === "G").length} Guru (heavy) · {result.syllables.filter(s => s.type === "L").length} Laghu (light)
                </div>
              </div>

              {/* Syllable Blocks */}
              <div className="rounded-2xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-white/8 border-black/6 p-6 shadow-md">
                <div className="flex items-center gap-3 mb-5">
                  <span className="text-xs font-semibold uppercase tracking-widest dark:text-gray-400 text-gray-500">Syllable Analysis</span>
                  <div className="flex gap-3 ml-auto">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded dark:bg-amber-500/30 bg-amber-200" />
                      <span className="text-xs dark:text-gray-400 text-gray-500">G = Guru (Heavy)</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded dark:bg-cyan-500/30 bg-cyan-200" />
                      <span className="text-xs dark:text-gray-400 text-gray-500">L = Laghu (Light)</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {result.syllables.map((syl, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.7, y: 10 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.04, ease: [0.22, 1, 0.36, 1] }}
                      className={`relative flex flex-col items-center rounded-xl px-3 py-2 min-w-[44px] border ${
                        syl.type === "G"
                          ? "dark:bg-amber-500/12 bg-amber-50 dark:border-amber-500/30 border-amber-200"
                          : "dark:bg-cyan-500/12 bg-cyan-50 dark:border-cyan-500/30 border-cyan-200"
                      }`}
                    >
                      <span
                        className="text-base font-bold dark:text-white text-gray-800 leading-none mb-1"
                        style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
                      >
                        {syl.text}
                      </span>
                      <span
                        className={`text-[10px] font-bold tracking-wider ${
                          syl.type === "G" ? "dark:text-amber-400 text-amber-600" : "dark:text-cyan-400 text-cyan-600"
                        }`}
                      >
                        {syl.type}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}