// ==========================================
// IMPORTS
// ==========================================
import { useEffect, useRef } from "react";

// The Props we expect from AudioSection.tsx
interface AudioWaveformProps {
  audioRef?: React.RefObject<HTMLAudioElement | null>; // The physical audio file element
  playing: boolean;
  bars?: number;
  className?: string;
  color?: "amber" | "cyan" | "violet";
}

export default function AudioWaveform({ audioRef, playing, bars = 80, className = "", color = "amber" }: AudioWaveformProps) {
  
  // ==========================================
  // COLOR THEMES
  // ==========================================
  const colorMap = {
    amber: { from: "#f59e0b", to: "#fbbf24" },
    cyan: { from: "#06b6d4", to: "#22d3ee" },
    violet: { from: "#8b5cf6", to: "#a78bfa" },
  };
  const { from, to } = colorMap[color];

  // ==========================================
  // HIGH-PERFORMANCE REFS (Bypassing React)
  // ==========================================
  // Why use Refs instead of React State?
  // Updating React State 60 times a second causes huge lag. 
  // Instead, we store a direct "pointer" to every single HTML bar in this array.
  // This allows us to inject CSS heights instantly without asking React to redraw the whole page!
  const barRefs = useRef<(HTMLDivElement | null)[]>([]);
  
  // Web Audio API Tools:
  const audioCtxRef = useRef<AudioContext | null>(null); // The master audio brain
  const analyserRef = useRef<AnalyserNode | null>(null); // The tool that measures frequency volumes
  const dataArrayRef = useRef<Uint8Array | null>(null);  // The array where the volume math is stored
  const animationRef = useRef<number>(0);                // The ID for our 60fps loop

  // ==========================================
  // TRUE REAL-TIME SYNC ENGINE
  // ==========================================
  useEffect(() => {
    // If we haven't received the audio element yet, stop.
    if (!audioRef || !audioRef.current) return;

    // ------------------------------------------
    // 1. INITIALIZE THE AUDIO CONTEXT
    // ------------------------------------------
    // We only create this once, right when the user clicks "Play".
    if (playing && !audioCtxRef.current) {
      // Connect to the browser's built-in audio system
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      audioCtxRef.current = new AudioContextClass();
      
      // Create an Analyser Node (think of it like a microphone listening to the file)
      analyserRef.current = audioCtxRef.current.createAnalyser();
      // fftSize controls how detailed the frequencies are. 256 gives us 128 distinct bands.
      analyserRef.current.fftSize = 256; 
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);

      // Connect the invisible <audio> tag into our Web Audio system
      const audioElement = audioRef.current as any;
      
      // We use __sourceConnected to prevent React Strict Mode from plugging the cables in twice
      if (!audioElement.__sourceConnected) {
        // Plug the audio into the Analyser
        const source = audioCtxRef.current.createMediaElementSource(audioRef.current);
        source.connect(analyserRef.current);
        // Plug the Analyser into the final speakers
        analyserRef.current.connect(audioCtxRef.current.destination);
        audioElement.__sourceConnected = true;
      }
    }

    // ------------------------------------------
    // 2. THE 60-FPS RENDERING LOOP
    // ------------------------------------------
    const renderFrame = () => {
      // Only draw the wave if music is playing
      if (analyserRef.current && dataArrayRef.current && playing) {
        
        // This command forces the Analyser to take a snapshot of the current sound frequencies
        // Note: We use "as any" to prevent a strict TypeScript error
        analyserRef.current.getByteFrequencyData(dataArrayRef.current as any);

        // Loop through all 80 of our UI bars
        for (let i = 0; i < bars; i++) {
          if (barRefs.current[i]) {
            // Get the live volume for this specific bar (number from 0 to 255)
            const value = dataArrayRef.current[i];
            
            // Calculate a percentage. We set a minimum of 5% so silent parts don't fully disappear.
            const percent = Math.max(5, (value / 255) * 100);
            
            // Push that exact percentage directly into the HTML element's CSS!
            barRefs.current[i]!.style.height = `${percent}%`;
          }
        }
      }
      
      // Tell the browser to run this exact function again on the next monitor refresh (60 times a sec)
      animationRef.current = requestAnimationFrame(renderFrame);
    };

    // ------------------------------------------
    // 3. START/STOP LOGIC
    // ------------------------------------------
    if (playing) {
      // Browsers often put audio to sleep to save battery. This wakes it up.
      if (audioCtxRef.current?.state === "suspended") {
        audioCtxRef.current.resume();
      }
      // Start the 60fps loop
      renderFrame();
    } else {
      // If the user clicks pause, instantly kill the 60fps loop
      cancelAnimationFrame(animationRef.current);
      
      // Smoothly lower all the bars back down to 5% flat when paused
      for (let i = 0; i < bars; i++) {
        if (barRefs.current[i]) {
          barRefs.current[i]!.style.height = "5%";
        }
      }
    }

    // Cleanup: If the component is destroyed, kill the loop so it doesn't run forever
    return () => cancelAnimationFrame(animationRef.current);
  }, [playing, audioRef, bars]);

  // ==========================================
  // RENDER UI
  // ==========================================
  return (
    <div className={`flex items-center justify-center gap-[3px] h-full ${className}`}>
      {/* Generate 80 empty divs */}
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          // 🔥 MAGIC TRICK: As React builds each div, we save a direct memory pointer to it in our 'barRefs' array.
          // Note: The { } braces are required to stop TypeScript from complaining about the return type.
          ref={(el) => { barRefs.current[i] = el; }}
          
          // Tailwind handles the smooth color gradients and CSS transitions
          className="rounded-full flex-shrink-0 transition-all duration-75"
          style={{
            width: "3px",
            height: "5%", // The flat starting point
            background: `linear-gradient(to top, ${from}, ${to})`,
            transformOrigin: "center", // Make the bar grow up and down from the center
          }}
        />
      ))}
    </div>
  );
}