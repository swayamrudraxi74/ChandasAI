import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Code2 } from "lucide-react";

interface PipelineStep {
  id: string;
  label: string;
  emoji: string;
  color: string;
  borderColor: string;
  textColor: string;
  glowColor: string;
  tech: string;
  description: string;
  details: string[];
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "input",
    label: "Sanskrit Text",
    emoji: "📜",
    color: "dark:bg-amber-500/15 bg-amber-50",
    borderColor: "dark:border-amber-500/30 border-amber-200",
    textColor: "dark:text-amber-300 text-amber-700",
    glowColor: "shadow-amber-500/20",
    tech: "Unicode · Devanagari",
    description: "Raw Sanskrit verse input in Devanagari script, supporting IAST transliteration as fallback.",
    details: [
      "UTF-8 Devanagari encoding",
      "IAST transliteration support",
      "Pāda (quarter-verse) boundary detection",
      "Saṃhitā and Padapāṭha forms",
    ],
  },
  {
    id: "syllable",
    label: "Syllable Split",
    emoji: "⚡",
    color: "dark:bg-orange-500/15 bg-orange-50",
    borderColor: "dark:border-orange-500/30 border-orange-200",
    textColor: "dark:text-orange-300 text-orange-700",
    glowColor: "shadow-orange-500/20",
    tech: "Rule-based NLP",
    description: "Phonological segmentation using traditional Śikṣā rules for vowel classification.",
    details: [
      "Sandhi resolution engine",
      "Vowel length detection (Hrasva / Dīrgha)",
      "Consonant cluster analysis",
      "Position-in-word metrics",
    ],
  },
  {
    id: "chandas",
    label: "Chandas Engine",
    emoji: "🔮",
    color: "dark:bg-cyan-500/15 bg-cyan-50",
    borderColor: "dark:border-cyan-500/30 border-cyan-200",
    textColor: "dark:text-cyan-300 text-cyan-700",
    glowColor: "shadow-cyan-500/20",
    tech: "Pattern Matching · ML",
    description: "Laghu-Guru classification and metre identification using Piṅgala's chandaḥśāstra.",
    details: [
      "Piṅgala's mātrika system",
      "Gaṇa pattern recognition",
      "50+ classical metres catalogued",
      "AI anomaly detection for mixed metres",
    ],
  },
  {
    id: "melody",
    label: "Melody Engine",
    emoji: "🎵",
    color: "dark:bg-violet-500/15 bg-violet-50",
    borderColor: "dark:border-violet-500/30 border-violet-200",
    textColor: "dark:text-violet-300 text-violet-700",
    glowColor: "shadow-violet-500/20",
    tech: "DSP · Pitch Mapping",
    description: "Maps syllable patterns to Sāmaveda pitch contours using swara theory.",
    details: [
      "Saptasvara pitch mapping (Sa-Re-Ga-Ma-Pa-Dha-Ni)",
      "Anudātta / Udātta / Svarita tones",
      "Laghu → lower pitch, Guru → higher pitch",
      "Sine, Crescendo, Vibrato synthesis modes",
    ],
  },
  {
    id: "audio",
    label: "Audio Synthesis",
    emoji: "🔊",
    color: "dark:bg-emerald-500/15 bg-emerald-50",
    borderColor: "dark:border-emerald-500/30 border-emerald-200",
    textColor: "dark:text-emerald-300 text-emerald-700",
    glowColor: "shadow-emerald-500/20",
    tech: "Web Audio API · WAV",
    description: "Real-time audio generation producing recitation-quality WAV output.",
    details: [
      "44.1 kHz sample rate",
      "Web Audio API oscillator synthesis",
      "Envelope shaping per syllable",
      "Downloadable WAV export",
    ],
  },
];

export default function PipelineSection() {
  const [hoveredStep, setHoveredStep] = useState<string | null>(null);

  return (
    <section id="pipeline" className="py-24 px-6 relative">
      {/* Ambient */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] dark:bg-indigo-600/6 bg-indigo-100/20 blur-[100px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full dark:bg-indigo-500/10 bg-indigo-100 dark:border border dark:border-indigo-500/20 border-indigo-300/40 mb-4">
            <Code2 className="w-3.5 h-3.5 text-indigo-500" />
            <span className="text-xs font-semibold tracking-widest uppercase dark:text-indigo-400 text-indigo-700">
              Technical Architecture
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold dark:text-white text-gray-900 mb-4">
            Processing Pipeline
          </h2>
          <p className="dark:text-gray-400 text-gray-500 max-w-lg mx-auto">
            A five-stage intelligent pipeline from raw Sanskrit input to synthesized audio — built on classical śāstra and modern AI.
          </p>
          <p className="dark:text-gray-500 text-gray-400 text-sm mt-2">
            Hover over each stage to explore the technical details
          </p>
        </motion.div>

        {/* Pipeline flow */}
        <div className="flex flex-col lg:flex-row items-stretch gap-0 lg:gap-0">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={step.id} className="flex flex-col lg:flex-row items-center flex-1 min-w-0">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
                className="relative flex-1 w-full"
                onMouseEnter={() => setHoveredStep(step.id)}
                onMouseLeave={() => setHoveredStep(null)}
              >
                <motion.div
                  whileHover={{ y: -4, scale: 1.02 }}
                  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                  className={`relative rounded-2xl ${step.color} border ${step.borderColor} p-5 cursor-default shadow-sm ${
                    hoveredStep === step.id ? `shadow-lg ${step.glowColor}` : ""
                  } transition-shadow duration-300`}
                >
                  {/* Step number */}
                  <div className={`text-[10px] font-bold uppercase tracking-widest mb-2 ${step.textColor} opacity-60`}>
                    {String(i + 1).padStart(2, "0")}
                  </div>

                  <div className="text-2xl mb-2">{step.emoji}</div>
                  <div className={`font-bold text-sm dark:text-white text-gray-900 mb-1`}>{step.label}</div>
                  <div className={`text-[10px] font-mono ${step.textColor} opacity-80`}>{step.tech}</div>

                  {/* Popover detail card */}
                  <AnimatePresence>
                    {hoveredStep === step.id && (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 rounded-2xl dark:bg-[rgba(12,16,35,0.98)] bg-white border dark:border-white/12 border-black/8 p-4 shadow-2xl z-30"
                      >
                        {/* Arrow */}
                        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-3 h-2 overflow-hidden">
                          <div className="w-3 h-3 dark:bg-[rgba(12,16,35,0.98)] bg-white border-r border-b dark:border-white/12 border-black/8 rotate-45 -translate-y-1.5" />
                        </div>

                        <div className={`text-xs font-bold mb-2 ${step.textColor}`}>{step.label}</div>
                        <p className="text-xs dark:text-gray-400 text-gray-500 mb-3 leading-relaxed">{step.description}</p>
                        <ul className="space-y-1">
                          {step.details.map((d) => (
                            <li key={d} className="flex items-start gap-2 text-[11px] dark:text-gray-400 text-gray-500">
                              <div className={`w-1 h-1 rounded-full mt-1.5 flex-shrink-0 ${step.textColor}`} style={{ background: "currentColor" }} />
                              {d}
                            </li>
                          ))}
                        </ul>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </motion.div>

              {/* Arrow connector */}
              {i < PIPELINE_STEPS.length - 1 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.1 + 0.3 }}
                  className="flex-shrink-0 flex items-center justify-center w-10 h-10 lg:h-auto"
                >
                  <div className="relative">
                    <ArrowRight className="w-5 h-5 dark:text-gray-600 text-gray-300" />
                    {/* Animated dot on arrow */}
                    <motion.div
                      className="absolute top-1/2 left-0 w-1.5 h-1.5 rounded-full dark:bg-amber-400 bg-amber-500 -translate-y-1/2"
                      animate={{ x: [0, 18, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: i * 0.4 }}
                    />
                  </div>
                </motion.div>
              )}
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
