import { motion } from "framer-motion";
import { ArrowRight, ChevronDown, Brain, Music } from "lucide-react";
import FloatingParticles from "./FloatingParticles";
import AudioWaveform from "./AudioWaveform";
import PitchMiniGraph from "./PitchMiniGraph";
import VedicBackground from "./VedicBackground";

interface HeroProps {
  onAnalyze: () => void;
  onExplore: () => void;
}

const FEATURE_CARDS = [
  {
    icon: "🔍",
    title: "Chandas Analysis",
    desc: "Precise syllable classification using traditional Laghu-Guru metrics",
    color: "amber",
  },
  {
    icon: "🎵",
    title: "Swara Intelligence",
    desc: "AI-powered melodic mapping aligned to Vedic pitch traditions",
    color: "cyan",
  },
  {
    icon: "🔊",
    title: "Audio Synthesis",
    desc: "Generates recitation-quality audio with authentic pitch contours",
    color: "violet",
  },
];

export default function HeroSection({ onAnalyze, onExplore }: HeroProps) {
  return (
    <section
      id="home"
      className="relative min-h-screen flex flex-col items-center justify-start overflow-hidden pt-24"
    >
      {/* Layer 1: AI-generated Vedic mandala photo background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <img
          src="/vedic-bg.png"
          alt=""
          className="absolute inset-0 w-full h-full object-cover object-center"
          style={{ opacity: 0.22, mixBlendMode: "multiply" }}
        />
        {/* Soft white overlay to keep text readable */}
        <div className="absolute inset-0 bg-gradient-to-b from-amber-50/70 via-amber-50/50 to-amber-50/80" />
      </div>

      {/* Layer 2: Vedic SVG/text overlay animations */}
      <VedicBackground variant="hero" />

      {/* Layer 3: Ambient colour glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[700px] h-[700px] rounded-full bg-amber-300/15 blur-[140px] glow-pulse" />
        <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full bg-orange-200/12 blur-[120px] glow-pulse" style={{ animationDelay: "2s" }} />
        <div className="absolute bottom-1/4 left-1/2 w-[400px] h-[400px] rounded-full bg-amber-400/10 blur-[100px] glow-pulse" style={{ animationDelay: "1s" }} />
      </div>

      <FloatingParticles count={30} />

      <div className="relative z-10 max-w-6xl mx-auto px-6 flex flex-col items-center text-center">
        {/* Title area with mandala glow behind */}
        <div className="relative mb-4">
          {/* Mandala glow */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none -z-10">
            <div className="w-[420px] h-[420px] mandala-rotate opacity-[0.06] dark:opacity-[0.08]">
              <svg viewBox="0 0 400 400" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="200" cy="200" r="190" stroke="url(#mandalaGrad)" strokeWidth="0.5"/>
                <circle cx="200" cy="200" r="160" stroke="url(#mandalaGrad)" strokeWidth="0.5"/>
                <circle cx="200" cy="200" r="130" stroke="url(#mandalaGrad)" strokeWidth="0.5"/>
                <circle cx="200" cy="200" r="100" stroke="url(#mandalaGrad)" strokeWidth="0.5"/>
                <circle cx="200" cy="200" r="70" stroke="url(#mandalaGrad)" strokeWidth="0.5"/>
                {Array.from({ length: 16 }).map((_, i) => {
                  const angle = (i * 360) / 16;
                  const rad = (angle * Math.PI) / 180;
                  return (
                    <line
                      key={i}
                      x1={200 + 10 * Math.cos(rad)}
                      y1={200 + 10 * Math.sin(rad)}
                      x2={200 + 190 * Math.cos(rad)}
                      y2={200 + 190 * Math.sin(rad)}
                      stroke="url(#mandalaGrad)"
                      strokeWidth="0.5"
                    />
                  );
                })}
                {Array.from({ length: 8 }).map((_, i) => {
                  const angle = (i * 360) / 8;
                  const rad = (angle * Math.PI) / 180;
                  const x = 200 + 130 * Math.cos(rad);
                  const y = 200 + 130 * Math.sin(rad);
                  return <circle key={i} cx={x} cy={y} r="8" stroke="url(#mandalaGrad)" strokeWidth="0.5" />;
                })}
                <defs>
                  <radialGradient id="mandalaGrad" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f59e0b" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </radialGradient>
                </defs>
              </svg>
            </div>
          </div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="shimmer-text text-6xl md:text-7xl lg:text-8xl font-black tracking-tight leading-tight"
            style={{
              background: "linear-gradient(135deg, #f59e0b 0%, #fbbf24 25%, #e0f2fe 50%, #06b6d4 75%, #f59e0b 100%)",
              backgroundSize: "200% auto",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            ChandasAI
          </motion.h1>
        </div>

        {/* Subtitle badge — below the main title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="flex items-center gap-2 px-4 py-2 rounded-full mb-8 dark:bg-amber-500/10 bg-amber-100 dark:border dark:border-amber-500/20 border border-amber-300/50"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
          <span className="text-xs font-semibold tracking-widest uppercase dark:text-amber-400 text-amber-700">
            Indian Knowledge System
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="text-xl md:text-2xl dark:text-gray-300 text-gray-600 max-w-2xl mx-auto mb-4 leading-relaxed"
        >
          Ancient wisdom meets artificial intelligence.
        </motion.p>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="text-base dark:text-gray-500 text-gray-400 max-w-xl mx-auto mb-10"
        >
          Analyze Sanskrit verses, detect metrical patterns, map melodic pitch, and generate authentic recitation audio — powered by AI.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.6 }}
          className="flex flex-wrap gap-4 justify-center mb-12"
        >
          <motion.button
            whileHover={{ scale: 1.03, boxShadow: "0 0 32px rgba(245,158,11,0.4)" }}
            whileTap={{ scale: 0.97 }}
            onClick={onAnalyze}
            className="flex items-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold text-base shadow-lg transition-all duration-300"
          >
            Analyze a Verse
            <ArrowRight className="w-4 h-4" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onExplore}
            className="flex items-center gap-2 px-8 py-4 rounded-2xl dark:bg-white/5 bg-black/5 dark:border border dark:border-white/10 border-black/10 dark:text-gray-200 text-gray-700 font-semibold text-base backdrop-blur-sm transition-all duration-300 dark:hover:bg-white/10 hover:bg-black/10"
          >
            Explore Architecture
            <ChevronDown className="w-4 h-4" />
          </motion.button>
        </motion.div>

        {/* Audio waveform */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0.8 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="mb-16"
        >
          <AudioWaveform playing={true} bars={64} className="h-12 opacity-70" />
        </motion.div>
      </div>

      {/* Floating intelligence cards */}
      <div className="absolute left-6 lg:left-16 top-1/2 -translate-y-1/2 hidden lg:block float-slow z-10">
        <motion.div
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 1.0 }}
          className="w-52 rounded-2xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-amber-500/20 border-amber-200/60 p-4 shadow-xl"
        >
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-semibold dark:text-amber-400 text-amber-600 tracking-wide">Chandas Detection</span>
          </div>
          <div className="flex gap-1.5 flex-wrap">
            {["ल", "ग", "ग", "ल", "ल", "ग", "ल", "ग"].map((sym, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.2 + i * 0.08 }}
                className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                  sym === "ल"
                    ? "dark:bg-cyan-500/20 bg-cyan-100 dark:text-cyan-300 text-cyan-600"
                    : "dark:bg-amber-500/20 bg-amber-100 dark:text-amber-300 text-amber-600"
                }`}
              >
                {sym}
              </motion.div>
            ))}
          </div>
          <div className="mt-2 text-[10px] dark:text-gray-500 text-gray-400">Anuṣṭubh · 8 syllables/pāda</div>
        </motion.div>
      </div>

      <div className="absolute right-6 lg:right-16 top-1/2 -translate-y-1/2 hidden lg:block float-slow-reverse z-10">
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 1.0 }}
          className="w-52 rounded-2xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-cyan-500/20 border-cyan-200/60 p-4 shadow-xl"
        >
          <div className="flex items-center gap-2 mb-3">
            <Music className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-semibold dark:text-cyan-400 text-cyan-600 tracking-wide">Melody Mapping</span>
          </div>
          <PitchMiniGraph animated />
          <div className="mt-2 text-[10px] dark:text-gray-500 text-gray-400">Pitch contour · Sine wave</div>
        </motion.div>
      </div>

      {/* Feature cards */}
      <div className="relative z-10 w-full max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FEATURE_CARDS.map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.9 + i * 0.15, ease: [0.22, 1, 0.36, 1] }}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="rounded-2xl dark:bg-[rgba(15,20,45,0.6)] bg-white/70 backdrop-blur-xl dark:border border dark:border-white/8 border-black/6 p-6 cursor-default shadow-sm dark:shadow-none"
            >
              <div className="text-3xl mb-3">{card.icon}</div>
              <h3 className="font-bold dark:text-white text-gray-900 mb-2">{card.title}</h3>
              <p className="text-sm dark:text-gray-400 text-gray-500 leading-relaxed">{card.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
