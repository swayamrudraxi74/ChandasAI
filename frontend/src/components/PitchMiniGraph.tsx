import { motion } from "framer-motion";

interface PitchMiniGraphProps {
  animated?: boolean;
  heights?: number[];
}

const DEFAULT_HEIGHTS = [30, 50, 80, 60, 90, 70, 45, 85, 55, 40];

export default function PitchMiniGraph({ animated = false, heights = DEFAULT_HEIGHTS }: PitchMiniGraphProps) {
  return (
    <div className="flex items-end gap-1 h-12">
      {heights.map((h, i) => (
        <motion.div
          key={i}
          className="flex-1 rounded-t-sm"
          style={{
            background: "linear-gradient(to top, #06b6d4, #22d3ee)",
            transformOrigin: "bottom",
            height: "100%",
          }}
          initial={{ scaleY: 0 }}
          animate={
            animated
              ? { scaleY: [h / 100, (h * 0.6) / 100, h / 100, (h * 1.2) / 100, h / 100] }
              : { scaleY: h / 100 }
          }
          transition={
            animated
              ? { duration: 2, delay: i * 0.15, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.5, delay: i * 0.05 }
          }
        />
      ))}
    </div>
  );
}
