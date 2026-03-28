import { motion } from "framer-motion";

const SHLOKAS = [
  "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
  "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
  "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत",
  "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्",
  "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं",
  "असतो मा सद्गमय तमसो मा ज्योतिर्गमय",
  "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः",
  "ॐ तत्सत् ब्रह्मार्पणमस्तु",
  "छन्दसां मातरं वाचम्",
  "अक्षरं परमं ब्रह्म",
];

const LAGHU_GURU = ["ल", "ग", "ल", "ल", "ग", "ग", "ल", "ग", "ल", "ल", "ग"];

interface VedicBackgroundProps {
  variant?: "hero" | "light";
}

export default function VedicBackground({ variant = "hero" }: VedicBackgroundProps) {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none select-none">

      {/* === LAYER 1: Large faded Sanskrit shlokas scattered across bg === */}
      <div className="absolute inset-0">
        {SHLOKAS.map((shloka, i) => {
          const top = 5 + ((i * 97) % 90);
          const left = (i * 37) % 75;
          const size = 10 + (i % 4) * 4;
          const rotate = -8 + (i % 5) * 4;
          const opacity = variant === "hero" ? 0.025 + (i % 3) * 0.008 : 0.04 + (i % 3) * 0.01;
          return (
            <div
              key={i}
              className="absolute dark:text-amber-200 text-amber-900 font-bold whitespace-nowrap"
              style={{
                top: `${top}%`,
                left: `${left}%`,
                fontSize: `${size}px`,
                transform: `rotate(${rotate}deg)`,
                opacity,
                fontFamily: "'Noto Serif Devanagari', Georgia, serif",
                letterSpacing: "0.05em",
              }}
            >
              {shloka}
            </div>
          );
        })}
      </div>

      {/* === LAYER 2: Large OM symbols === */}
      {[
        { top: "8%", left: "2%", size: 220, opacity: 0.03 },
        { top: "15%", right: "3%", size: 180, opacity: 0.025 },
        { top: "60%", left: "5%", size: 150, opacity: 0.02 },
        { top: "70%", right: "2%", size: 200, opacity: 0.03 },
      ].map((pos, i) => (
        <div
          key={i}
          className="absolute dark:text-amber-300 text-amber-700 font-black leading-none"
          style={{
            top: pos.top,
            left: "left" in pos ? pos.left : undefined,
            right: "right" in pos ? (pos as { right?: string }).right : undefined,
            fontSize: `${pos.size}px`,
            opacity: pos.opacity,
            fontFamily: "'Noto Serif Devanagari', Georgia, serif",
          }}
        >
          ॐ
        </div>
      ))}

      {/* === LAYER 3: SVG Mandala rings scattered === */}
      {[
        { cx: "12%", cy: "25%", r: 160, opacity: 0.04 },
        { cx: "88%", cy: "20%", r: 120, opacity: 0.035 },
        { cx: "50%", cy: "80%", r: 200, opacity: 0.03 },
        { cx: "25%", cy: "70%", r: 90, opacity: 0.04 },
        { cx: "75%", cy: "65%", r: 140, opacity: 0.03 },
      ].map((m, i) => (
        <svg
          key={i}
          className="absolute"
          style={{ left: m.cx, top: m.cy, transform: "translate(-50%, -50%)", opacity: m.opacity }}
          width={m.r * 2}
          height={m.r * 2}
          viewBox={`0 0 ${m.r * 2} ${m.r * 2}`}
        >
          <circle cx={m.r} cy={m.r} r={m.r - 4} stroke="#f59e0b" strokeWidth="0.5" fill="none" />
          <circle cx={m.r} cy={m.r} r={m.r * 0.8} stroke="#f59e0b" strokeWidth="0.5" fill="none" />
          <circle cx={m.r} cy={m.r} r={m.r * 0.6} stroke="#06b6d4" strokeWidth="0.5" fill="none" />
          <circle cx={m.r} cy={m.r} r={m.r * 0.4} stroke="#f59e0b" strokeWidth="0.5" fill="none" />
          <circle cx={m.r} cy={m.r} r={m.r * 0.2} stroke="#06b6d4" strokeWidth="0.5" fill="none" />
          {Array.from({ length: 12 }).map((_, j) => {
            const ang = (j * 30 * Math.PI) / 180;
            return (
              <line
                key={j}
                x1={m.r + (m.r * 0.15) * Math.cos(ang)}
                y1={m.r + (m.r * 0.15) * Math.sin(ang)}
                x2={m.r + (m.r - 4) * Math.cos(ang)}
                y2={m.r + (m.r - 4) * Math.sin(ang)}
                stroke="#f59e0b"
                strokeWidth="0.4"
              />
            );
          })}
          {Array.from({ length: 8 }).map((_, j) => {
            const ang = (j * 45 * Math.PI) / 180;
            const px = m.r + m.r * 0.55 * Math.cos(ang);
            const py = m.r + m.r * 0.55 * Math.sin(ang);
            return <circle key={j} cx={px} cy={py} r={4} stroke="#f59e0b" strokeWidth="0.4" fill="none" />;
          })}
        </svg>
      ))}

      {/* === LAYER 4: Floating Laghu-Guru pattern strip === */}
      <div className="absolute bottom-[10%] left-0 right-0 flex justify-center gap-3 opacity-[0.06]">
        {LAGHU_GURU.concat(LAGHU_GURU).map((sym, i) => (
          <span
            key={i}
            className="dark:text-cyan-300 text-cyan-700 font-bold"
            style={{ fontSize: "28px", fontFamily: "'Noto Serif Devanagari', Georgia, serif" }}
          >
            {sym}
          </span>
        ))}
      </div>

      {/* === LAYER 5: Palm-leaf manuscript lines (horizontal subtle stripes) === */}
      <div className="absolute inset-0">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="absolute left-0 right-0 dark:border-t dark:border-amber-300/[0.02] border-t border-amber-900/[0.03]"
            style={{ top: `${15 + i * 14}%` }}
          />
        ))}
      </div>

      {/* === LAYER 6: Slow-rotating large central mandala === */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] opacity-[0.025]"
      >
        <svg viewBox="0 0 900 900" fill="none">
          {[420, 370, 320, 270, 220, 170, 120].map((r) => (
            <circle key={r} cx="450" cy="450" r={r} stroke="#f59e0b" strokeWidth="0.5" />
          ))}
          {Array.from({ length: 24 }).map((_, i) => {
            const ang = (i * 15 * Math.PI) / 180;
            return (
              <line
                key={i}
                x1={450 + 30 * Math.cos(ang)}
                y1={450 + 30 * Math.sin(ang)}
                x2={450 + 420 * Math.cos(ang)}
                y2={450 + 420 * Math.sin(ang)}
                stroke="#f59e0b"
                strokeWidth="0.3"
              />
            );
          })}
          {Array.from({ length: 12 }).map((_, i) => {
            const ang = (i * 30 * Math.PI) / 180;
            const x = 450 + 320 * Math.cos(ang);
            const y = 450 + 320 * Math.sin(ang);
            return <circle key={i} cx={x} cy={y} r="12" stroke="#06b6d4" strokeWidth="0.4" fill="none" />;
          })}
          {Array.from({ length: 6 }).map((_, i) => {
            const ang = (i * 60 * Math.PI) / 180;
            const x = 450 + 200 * Math.cos(ang);
            const y = 450 + 200 * Math.sin(ang);
            return <circle key={i} cx={x} cy={y} r="20" stroke="#f59e0b" strokeWidth="0.4" fill="none" />;
          })}
        </svg>
      </motion.div>

      {/* === LAYER 7: Corner decorative Sanskrit numerals / syllables === */}
      {["अ", "इ", "उ", "ऋ"].map((aksara, i) => {
        const positions = [
          { top: "3%", left: "2%" },
          { top: "3%", right: "2%" },
          { bottom: "3%", left: "2%" },
          { bottom: "3%", right: "2%" },
        ];
        const p = positions[i];
        return (
          <div
            key={aksara}
            className="absolute dark:text-amber-400/10 text-amber-700/10 font-black"
            style={{
              ...p,
              fontSize: "80px",
              fontFamily: "'Noto Serif Devanagari', Georgia, serif",
            }}
          >
            {aksara}
          </div>
        );
      })}
    </div>
  );
}
