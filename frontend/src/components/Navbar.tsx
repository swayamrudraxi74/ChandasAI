import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";

interface NavbarProps {
  onHome: () => void;
  onInput: () => void;
  onMelody: () => void;
  onAudio: () => void;
  onPipeline: () => void;
}

export default function Navbar({ onHome, onInput, onMelody, onAudio, onPipeline }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.remove("dark");
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Home", action: onHome },
    { label: "Input & Analysis", action: onInput },
    { label: "Melody", action: onMelody },
    { label: "Audio", action: onAudio },
    { label: "Pipeline", action: onPipeline },
  ];

  return (
    <motion.nav
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-[rgba(255,250,240,0.90)] backdrop-blur-xl border-b border-border/30 shadow-lg"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <button onClick={onHome} className="flex items-center gap-3 group">
          <div className="relative w-9 h-9">
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 opacity-80 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-[2px] rounded-full bg-amber-50 flex items-center justify-center">
              <span className="text-sm font-bold text-amber-500">ॐ</span>
            </div>
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-gray-900">
              Chandas<span className="text-amber-500">AI</span>
            </span>
            <div className="text-[10px] text-amber-600/60 font-medium tracking-widest uppercase -mt-0.5">
              Sanskrit Intelligence
            </div>
          </div>
        </button>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={link.action}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-amber-600 transition-colors duration-200 rounded-lg hover:bg-black/5"
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Right: mobile menu only */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-black/5 transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-[rgba(255,250,240,0.95)] backdrop-blur-xl border-b border-border/30"
          >
            <div className="px-6 py-4 flex flex-col gap-1">
              {navLinks.map((link) => (
                <button
                  key={link.label}
                  onClick={() => { link.action(); setMobileOpen(false); }}
                  className="px-4 py-3 text-sm font-medium text-gray-600 hover:text-amber-600 transition-colors text-left rounded-lg hover:bg-black/5"
                >
                  {link.label}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
