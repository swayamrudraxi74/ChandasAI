import { motion } from "framer-motion";
import { Github, Twitter, ExternalLink } from "lucide-react";
import FloatingParticles from "./FloatingParticles";

interface FooterProps {
  onInput: () => void;
}

export default function FooterSection({ onInput }: FooterProps) {
  return (
    <footer className="relative overflow-hidden dark:bg-[rgba(5,8,20,0.9)] bg-amber-50/80 dark:border-t border-t dark:border-white/6 border-black/5 py-20 px-6">
      <FloatingParticles count={20} />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] dark:bg-amber-500/4 bg-amber-200/30 blur-[100px] pointer-events-none" />

      {/* Faint Sanskrit shloka in background */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden select-none">
        <div
          className="text-[180px] font-black dark:text-amber-500/3 text-amber-700/4 leading-none whitespace-nowrap"
          style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
        >
          ॐ
        </div>
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-sm font-bold text-white">
                ॐ
              </div>
              <div>
                <div className="font-black dark:text-white text-gray-900">
                  Chandas<span className="text-amber-500">AI</span>
                </div>
                <div className="text-[10px] dark:text-gray-600 text-gray-400 tracking-widest uppercase">Sanskrit Intelligence</div>
              </div>
            </div>
            <p className="text-sm dark:text-gray-500 text-gray-400 leading-relaxed max-w-xs">
              Bridging 3,000 years of Sanskrit metrical science with modern AI for the Indian Knowledge System research community.
            </p>
            <div className="flex gap-3 mt-5">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="w-9 h-9 rounded-xl dark:bg-white/5 bg-black/5 flex items-center justify-center dark:hover:bg-white/10 hover:bg-black/8 transition-colors"
              >
                <Github className="w-4 h-4 dark:text-gray-400 text-gray-500" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="w-9 h-9 rounded-xl dark:bg-white/5 bg-black/5 flex items-center justify-center dark:hover:bg-white/10 hover:bg-black/8 transition-colors"
              >
                <Twitter className="w-4 h-4 dark:text-gray-400 text-gray-500" />
              </motion.button>
            </div>
          </div>

          {/* Platform links */}
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest dark:text-gray-500 text-gray-400 mb-4">Platform</div>
            <div className="flex flex-col gap-2">
              <button
                onClick={onInput}
                className="text-sm dark:text-gray-400 text-gray-500 dark:hover:text-amber-400 hover:text-amber-600 transition-colors text-left flex items-center gap-2"
              >
                Analyze a Verse
              </button>
              {[
                "Classical Metres Database",
                "Swara Pitch Tables",
                "Piṅgala's Chandaḥśāstra",
                "IKS Research Papers",
              ].map((label) => (
                <div key={label} className="flex items-center gap-2">
                  <span className="text-sm dark:text-gray-400 text-gray-500 dark:hover:text-amber-400 hover:text-amber-600 transition-colors cursor-pointer">
                    {label}
                  </span>
                  <ExternalLink className="w-3 h-3 dark:text-gray-600 text-gray-400" />
                </div>
              ))}
            </div>
          </div>

          {/* Sanskrit wisdom */}
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest dark:text-gray-500 text-gray-400 mb-4">
              Vedic Wisdom
            </div>
            <div className="space-y-4">
              {[
                { shloka: "अक्षरं परमं ब्रह्म", trans: "The syllable is the supreme Brahman" },
                { shloka: "छन्दसां मातरं वाचम्", trans: "Speech is the mother of metres" },
                { shloka: "वेदो नित्यो महान् गुरुः", trans: "The Veda is the eternal great teacher" },
              ].map((item) => (
                <div key={item.shloka} className="rounded-xl dark:bg-amber-500/5 bg-amber-100/40 dark:border border dark:border-amber-500/10 border-amber-200/40 px-4 py-3">
                  <div
                    className="text-sm dark:text-amber-300/80 text-amber-700 font-semibold mb-1 leading-relaxed"
                    style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
                  >
                    {item.shloka}
                  </div>
                  <div className="text-[11px] dark:text-gray-600 text-gray-400 italic">{item.trans}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t dark:border-white/6 border-black/5 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs dark:text-gray-600 text-gray-400">
            © 2025 ChandasAI · Indian Knowledge System AI Research
          </p>
          <div className="flex items-center gap-4">
            <span
              className="text-xs dark:text-gray-600 text-gray-400"
              style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
            >
              सर्वे भवन्तु सुखिनः · May all beings be happy
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
