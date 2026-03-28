// ==========================================
// 1. IMPORTS
// ==========================================
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion"; // Used for smooth, complex animations
import { Music, Waves, TrendingUp, Activity } from "lucide-react"; // SVG Icons for our buttons and headers

// ==========================================
// 2. TYPES & INTERFACES (TypeScript Rules)
// ==========================================
// Defines exactly what a single syllable object looks like
type SyllableResult = { 
  text: string;     // The actual Sanskrit letter (e.g., "मा")
  type: "L" | "G"   // "L" for Laghu (short), "G" for Guru (long)
};

// Defines the data this entire component expects to receive from its parent
interface MelodySectionProps {
  syllables: SyllableResult[]; // Array of syllables from the analyzer
  metre: string;               // The name of the detected metre (e.g., "Anuṣṭubh")
}

// Restricts the pitch style to only these three specific string values
type PitchStyle = "sine" | "crescendo" | "vibrato";

// Configuration array for the 3 toggle buttons at the top of the graph
const PITCH_STYLES: { id: PitchStyle; label: string; icon: React.ReactNode; desc: string }[] = [
  { id: "sine", label: "Sine", icon: <Waves className="w-4 h-4" />, desc: "Smooth sinusoidal pitch wave" },
  { id: "crescendo", label: "Crescendo", icon: <TrendingUp className="w-4 h-4" />, desc: "Rising melodic arc" },
  { id: "vibrato", label: "Vibrato", icon: <Activity className="w-4 h-4" />, desc: "Oscillating pitch modulation" },
];

// ==========================================
// 3. THE MATH ENGINE (Calculates Bar Heights)
// ==========================================
function computePitchHeights(syllables: SyllableResult[], style: PitchStyle): number[] {
  // FALLBACK: If the user hasn't analyzed a verse yet (empty array), generate a fake pretty curve
  if (!syllables.length) {
    return Array.from({ length: 12 }, (_, i) => {
      // Uses basic Trigonometry (Math.sin) to make wavy lines for the placeholder
      if (style === "sine") return 40 + Math.sin(i * 0.6) * 35 + 25;
      if (style === "crescendo") return 20 + (i / 11) * 80;
      return 40 + Math.sin(i * 1.2) * 20 + Math.sin(i * 3) * 15 + 20;
    });
  }

  // REAL DATA: Map heights exactly based on the real Laghu/Guru types
  return syllables.map((s, i) => {
    // Core logic: Gurus are tall (75%), Laghus are short (35%)
    const base = s.type === "G" ? 75 : 35;
    
    // We add slight math variations (sine waves or linear progression) based on the 
    // selected "Style" button so it looks organic, but the base height stays true to L/G.
    if (style === "sine") return base + Math.sin(i * 0.5) * 15;
    if (style === "crescendo") return Math.min(100, base + (i / syllables.length) * 25);
    return base + Math.sin(i * 1.2) * 15 + Math.sin(i * 0.3) * 10;
  });
}

// ==========================================
// 4. MAIN COMPONENT
// ==========================================
export default function MelodySection({ syllables, metre }: MelodySectionProps) {
  // State to track which button is currently clicked (defaults to "sine")
  const [pitchStyle, setPitchStyle] = useState<PitchStyle>("sine");

  // Run our math function to get an array of numbers representing percentages (e.g., [45, 80, 32...])
  const pitchHeights = computePitchHeights(syllables, pitchStyle);
  
  // If we have real syllables from the user, use them. 
  // Otherwise, create an array of 12 fake Sanskrit letters so the UI doesn't look empty on page load.
  const displaySyllables = syllables.length > 0 ? syllables : Array.from({ length: 12 }, (_, i) => ({
    text: ["क", "र्", "म", "ण्", "ये", "वा", "धि", "का", "र", "स्", "ते", "मा"][i] ?? "•",
    type: (i % 3 === 1 ? "G" : "L") as "L" | "G",
  }));

  // ==========================================
  // 5. RENDER UI
  // ==========================================
  return (
    <section id="melody" className="py-24 px-6 relative">
      {/* Visual flair: Ambient glowing blob in the background */}
      <div className="absolute top-1/2 right-0 w-[500px] h-[500px] dark:bg-cyan-500/6 bg-cyan-200/15 blur-[120px] pointer-events-none" />

      <div className="max-w-5xl mx-auto relative z-10">
        
        {/* HEADER SECTION (Fades in on scroll) */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full dark:bg-cyan-500/10 bg-cyan-100 dark:border border dark:border-cyan-500/20 border-cyan-300/40 mb-4">
            <Music className="w-3.5 h-3.5 text-cyan-500" />
            <span className="text-xs font-semibold tracking-widest uppercase dark:text-cyan-400 text-cyan-700">
              Step 2: Melody Mapping
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold dark:text-white text-gray-900 mb-4">
            Melodic Pitch Visualization
          </h2>
          <p className="dark:text-gray-400 text-gray-500 max-w-lg mx-auto">
            Each syllable maps to a melodic pitch contour based on its Laghu/Guru classification and position in the metre.
          </p>
        </motion.div>

        {/* MAIN CARD (The dark box containing the graph) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="rounded-3xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-white/8 border-black/6 p-8 shadow-lg"
        >
          {/* STYLE TOGGLE BUTTONS */}
          <div className="flex flex-wrap gap-3 mb-8">
            {PITCH_STYLES.map((style) => (
              <button
                key={style.id}
                onClick={() => setPitchStyle(style.id)}
                // Conditional styling: Changes color if it is the actively selected button
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all duration-300 ${
                  pitchStyle === style.id
                    ? "dark:bg-cyan-500/20 bg-cyan-100 dark:border-cyan-500/40 border-cyan-400 dark:text-cyan-300 text-cyan-700"
                    : "dark:bg-white/3 bg-black/3 dark:border-white/8 border-black/6 dark:text-gray-400 text-gray-500 dark:hover:bg-white/8 hover:bg-black/5"
                }`}
              >
                {style.icon}
                {style.label}
              </button>
            ))}
            <div className="ml-auto text-xs dark:text-gray-500 text-gray-400 self-center">
              {PITCH_STYLES.find(s => s.id === pitchStyle)?.desc}
            </div>
          </div>

          {/* THE GRAPH AREA */}
          <div className="relative">
            
            {/* Y-AXIS LABELS (Fixed on the left side) */}
            <div className="absolute left-0 top-0 bottom-8 flex flex-col justify-between pr-2">
              {["Ni'", "Dha", "Pa", "Ma", "Ga", "Re", "Sa"].map((note) => (
                <span key={note} className="text-[10px] dark:text-gray-600 text-gray-400 font-mono">{note}</span>
              ))}
            </div>

            <div className="pl-8 pb-8">
              {/* THE SCROLL WINDOW: This wraps both bars and labels so they scroll horizontally together */}
              <div className="overflow-x-auto overflow-y-hidden custom-scrollbar pb-4">
                
                {/* THE STRETCH CONTAINER: Forces the bars and labels to be the exact same width */}
                <div className="w-max pr-8">
                  
                  {/* CHART BACKGROUND (Holds the bars and gridlines) */}
                  <div className="relative h-48 flex items-end gap-[3px] border-b dark:border-white/10 border-black/8">
                    
                    {/* Draws horizontal guide lines at 25%, 50%, and 75% height */}
                    {[0.25, 0.5, 0.75].map((frac) => (
                      <div
                        key={frac}
                        className="absolute left-0 right-0 border-t dark:border-white/5 border-black/4 pointer-events-none"
                        style={{ bottom: `${frac * 100}%` }}
                      />
                    ))}

                    {/* AnimatePresence handles the fade-out/fade-in when switching styles */}
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={pitchStyle} // Changing this key forces React to re-animate the whole list
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.4 }}
                        className="flex items-end gap-[3px] h-full"
                      >
                        {/* THE BARS: Loop through our calculated heights and draw a div for each */}
                        {pitchHeights.map((h, i) => {
                          const syl = displaySyllables[i] ?? { text: "•", type: "L" as const };
                          return (
                            <motion.div
                              key={i}
                              // Animate bars growing from the bottom up
                              initial={{ scaleY: 0, opacity: 0 }}
                              animate={{ scaleY: 1, opacity: 1 }}
                              transition={{ duration: 0.4, delay: i * 0.03, ease: [0.22, 1, 0.36, 1] }}
                              className="w-10 relative group"
                              style={{ height: "100%", transformOrigin: "bottom" }}
                            >
                              {/* The actual colored rectangle */}
                              <div
                                className={`absolute bottom-0 left-0 right-0 rounded-t-sm transition-all duration-500 ${
                                  syl.type === "G"
                                    ? "dark:bg-gradient-to-t dark:from-amber-600/60 dark:to-amber-400/90 bg-gradient-to-t from-amber-400 to-amber-300" // Guru Color (Amber/Gold)
                                    : "dark:bg-gradient-to-t dark:from-cyan-600/60 dark:to-cyan-400/90 bg-gradient-to-t from-cyan-400 to-cyan-300"   // Laghu Color (Cyan/Blue)
                                }`}
                                // Apply the math height we calculated earlier!
                                style={{ height: `${Math.min(100, Math.max(5, h))}%` }} 
                              />
                              
                              {/* HOVER TOOLTIP: Hidden by default, appears when mouse is over the bar */}
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                                <div className="dark:bg-gray-800 bg-white rounded-lg px-2 py-1 text-[10px] font-mono whitespace-nowrap shadow-lg border dark:border-white/10 border-black/8">
                                  <span className="dark:text-white text-gray-800">{syl.text}</span>
                                  <span className={`ml-1 ${syl.type === "G" ? "dark:text-amber-400 text-amber-600" : "dark:text-cyan-400 text-cyan-600"}`}>
                                    {syl.type} · {Math.round(h)}%
                                  </span>
                                </div>
                              </div>
                            </motion.div>
                          );
                        })}
                      </motion.div>
                    </AnimatePresence>
                  </div>

                  {/* X-AXIS LABELS: The Sanskrit syllables written under the bars */}
                  <div className="flex gap-[3px] mt-2">
                    {pitchHeights.map((_, i) => {
                      const syl = displaySyllables[i] ?? { text: "•" };
                      return (
                        <div key={i} className="w-10 text-center">
                          <span
                            className="text-[12px] dark:text-gray-300 text-gray-600 font-bold block"
                            style={{ fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
                          >
                            {syl.text}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* BOTTOM LEGEND */}
          <div className="flex gap-4 mt-2 pt-4 border-t dark:border-white/5 border-black/5">
            {/* Show metre name if one was detected */}
            {metre && (
              <div className="text-sm dark:text-gray-300 text-gray-600">
                <span className="dark:text-gray-500 text-gray-400">Metre:</span>{" "}
                <span className="font-semibold dark:text-amber-400 text-amber-600">{metre}</span>
              </div>
            )}
            
            {/* Color key */}
            <div className="flex gap-3 ml-auto">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm dark:bg-amber-400 bg-amber-400" />
                <span className="text-xs dark:text-gray-400 text-gray-500">Guru (High Pitch)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-sm dark:bg-cyan-400 bg-cyan-400" />
                <span className="text-xs dark:text-gray-400 text-gray-500">Laghu (Low Pitch)</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}