// ==========================================
// IMPORTS
// ==========================================
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, Download, Volume2, VolumeX, SkipBack, Headphones } from "lucide-react";
import AudioWaveform from "./AudioWaveform";

// Define the exact shape of the data we get from Step 1
type SyllableResult = { text: string; type: "L" | "G" };

interface AudioSectionProps {
  syllables: SyllableResult[];
  verse: string; // The raw Sanskrit string we send to Python
}

export default function AudioSection({ syllables, verse }: AudioSectionProps) {
  // ==========================================
  // STATE (React Memory)
  // ==========================================
  const [playing, setPlaying] = useState(false); // Is the song playing?
  const [muted, setMuted] = useState(false);     // Is it muted?
  const [progress, setProgress] = useState(0);   // The 0-100% value of the purple scrubber bar
  
  const [generating, setGenerating] = useState(false); // True while waiting for Python
  const [generated, setGenerated] = useState(false);   // True when the audio is ready
  
  const [audioUrl, setAudioUrl] = useState<string | null>(null); // The actual .wav file link
  const [waveform, setWaveform] = useState<number[]>([]);        // Legacy state for Librosa data
  
  // ==========================================
  // REFS (Direct HTML Element Access)
  // ==========================================
  // We use this to point directly to the invisible <audio> tag so we can play/pause it
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ==========================================
  // ENGINE 1: THE UI PROGRESS BAR
  // ==========================================
  // This effect runs in the background and updates the purple scrubber bar 
  // so it perfectly matches the real audio playback time.
  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        if (audioRef.current) {
          const current = audioRef.current.currentTime;
          const duration = audioRef.current.duration || 1;
          const percentage = (current / duration) * 100;
          
          setProgress(percentage);
          
          // Auto-stop when the song ends
          if (percentage >= 100) setPlaying(false);
        }
      }, 80);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing]);

  // ==========================================
  // ENGINE 2: THE RESET TRIGGER (🔥 THE FIX)
  // ==========================================
  // This listens for changes to the 'verse' prop. When a new verse is analyzed 
  // in the input section, this triggers automatically to reset the audio UI.
  useEffect(() => {
    // 🔄 RESET LOGIC: Revert the UI back to its initial state
    setGenerated(false);    // Hides the audio player, shows the "Synthesize Audio" button
    setAudioUrl(null);      // Clears out the old generated audio URL
    setPlaying(false);      // Ensures playback is marked as stopped
    setProgress(0);         // Resets the scrubber bar back to 0%

    // Physically stop the audio element and drop the old file from memory
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = ""; 
    }
  }, [verse]); // The dependency array: React runs this block EVERY time 'verse' changes.

  // ==========================================
  // ENGINE 3: PYTHON API CONNECTION
  // ==========================================
  const handleGenerate = async () => {
    if (!verse) return;
    setGenerating(true); // Show loading spinner
    
    try {
      // Ask Python to synthesize the voice
      const response = await fetch("http://127.0.0.1:8000/generate-audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: verse }),
      });

      if (!response.ok) throw new Error("Audio generation failed");
      
      const data = await response.json();
      
      // Save the generated file URL into React state
      setAudioUrl(data.audio_url); 
      setWaveform(data.waveform);  
      
      // Switch the UI from the "Generate" button to the "Player" view
      setGenerated(true);
      setProgress(0);
      
    } catch (error) {
      console.error(error);
      alert("Audio generation failed. Is your Python backend running?");
    } finally {
      setGenerating(false); // Hide loading spinner
    }
  };

  // ==========================================
  // MEDIA BUTTON CONTROLS
  // ==========================================
  const handlePlayPause = () => {
    if (!audioRef.current) return;
    
    if (playing) {
      audioRef.current.pause();
    } else {
      // If song is finished, restart from the beginning before playing
      if (progress >= 100) {
        setProgress(0);
        audioRef.current.currentTime = 0;
      }
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  const handleReset = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setPlaying(false);
    setProgress(0);
  };

  const formatTime = (pct: number) => {
    const total = audioRef.current?.duration || (syllables.length > 0 ? syllables.length * 0.4 : 8);
    const current = (pct / 100) * total;
    const pad = (n: number) => String(Math.floor(n)).padStart(2, "0");
    return `${pad(current / 60)}:${pad(current % 60)}`;
  };

  return (
    <section id="audio" className="py-24 px-6 relative">
      <div className="absolute bottom-0 left-0 w-[600px] h-[400px] dark:bg-violet-500/5 bg-violet-100/30 blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Title Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full dark:bg-violet-500/10 bg-violet-100 dark:border border dark:border-violet-500/20 border-violet-300/40 mb-4">
            <Headphones className="w-3.5 h-3.5 text-violet-500" />
            <span className="text-xs font-semibold tracking-widest uppercase dark:text-violet-400 text-violet-700">
              Step 3: Audio Output
            </span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold dark:text-white text-gray-900 mb-4">
            Recitation Audio
          </h2>
          <p className="dark:text-gray-400 text-gray-500 max-w-lg mx-auto">
            AI-synthesized recitation audio with authentic Vedic pitch contours, generated from the detected chandas pattern.
          </p>
        </motion.div>

        {/* Main Interface */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="rounded-3xl dark:bg-[rgba(15,20,45,0.7)] bg-white/80 backdrop-blur-xl dark:border border dark:border-white/8 border-black/6 p-8 shadow-lg"
        >
          {!generated ? (
            // VIEW 1: THE BIG GENERATE BUTTON
            <div className="flex flex-col items-center gap-6 py-8">
              <div className="w-20 h-20 rounded-full dark:bg-violet-500/15 bg-violet-100 flex items-center justify-center">
                <Headphones className="w-8 h-8 dark:text-violet-400 text-violet-600" />
              </div>
              <div className="text-center">
                <div className="text-xl font-bold dark:text-white text-gray-900 mb-2">Generate Recitation Audio</div>
                <div className="text-sm dark:text-gray-400 text-gray-500">
                  Click below to synthesize authentic Sanskrit recitation audio
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.03, boxShadow: "0 0 32px rgba(139,92,246,0.35)" }}
                whileTap={{ scale: 0.97 }}
                onClick={handleGenerate}
                disabled={generating}
                className="flex items-center gap-2.5 px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold shadow-lg disabled:opacity-70 transition-all duration-300"
              >
                {generating ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    />
                    Synthesizing audio...
                  </>
                ) : (
                  <>
                    <Headphones className="w-4 h-4" />
                    Synthesize Audio
                  </>
                )}
              </motion.button>
            </div>
          ) : (
            // VIEW 2: THE AUDIO PLAYER
            <div>
              <div className="relative mb-8 h-24 rounded-2xl dark:bg-white/3 bg-black/3 dark:border border dark:border-white/8 border-black/6 overflow-hidden flex items-center px-4">
                {/* Purple Progress Overlay */}
                <motion.div
                  className="absolute left-0 top-0 bottom-0 dark:bg-violet-500/10 bg-violet-100/50"
                  style={{ width: `${progress}%` }}
                  transition={{ duration: 0.1 }}
                />
                <div className="relative z-10 w-full h-full flex items-center">
                  {/* 🔥 WE PASS THE AUDIO REF DOWN TO THE WAVEFORM COMPONENT */}
                  <AudioWaveform audioRef={audioRef} playing={playing} bars={80} className="h-16 w-full" color="violet" />
                </div>
              </div>

              {/* Scrubber Bar */}
              <div className="flex items-center gap-3 mb-6">
                <span className="text-xs font-mono dark:text-gray-500 text-gray-400 w-10">{formatTime(progress)}</span>
                <div
                  className="flex-1 h-1.5 rounded-full dark:bg-white/10 bg-black/10 cursor-pointer relative overflow-hidden"
                  onClick={(e) => {
                    // Calculate click position to skip audio
                    const rect = e.currentTarget.getBoundingClientRect();
                    const pct = ((e.clientX - rect.left) / rect.width) * 100;
                    setProgress(Math.max(0, Math.min(100, pct)));
                    if (audioRef.current && audioRef.current.duration) {
                      audioRef.current.currentTime = (Math.max(0, Math.min(100, pct)) / 100) * audioRef.current.duration;
                    }
                  }}
                >
                  <motion.div
                    className="absolute left-0 top-0 bottom-0 rounded-full bg-gradient-to-r from-violet-500 to-purple-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-xs font-mono dark:text-gray-500 text-gray-400 w-10">{formatTime(100)}</span>
              </div>

              {/* Media Control Buttons */}
              <div className="flex items-center justify-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={handleReset}
                  className="w-10 h-10 rounded-full dark:bg-white/5 bg-black/5 flex items-center justify-center dark:hover:bg-white/10 hover:bg-black/10 transition-colors"
                >
                  <SkipBack className="w-4 h-4 dark:text-gray-300 text-gray-600" />
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05, boxShadow: "0 0 24px rgba(139,92,246,0.4)" }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handlePlayPause}
                  className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-purple-600 flex items-center justify-center shadow-lg"
                >
                  <AnimatePresence mode="wait">
                    {playing ? (
                      <motion.div key="pause" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}><Pause className="w-6 h-6 text-white" /></motion.div>
                    ) : (
                      <motion.div key="play" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}><Play className="w-6 h-6 text-white ml-0.5" /></motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                    setMuted(!muted);
                    if (audioRef.current) audioRef.current.muted = !muted;
                  }}
                  className="w-10 h-10 rounded-full dark:bg-white/5 bg-black/5 flex items-center justify-center dark:hover:bg-white/10 hover:bg-black/10 transition-colors"
                >
                  {muted ? <VolumeX className="w-4 h-4 dark:text-gray-300 text-gray-600" /> : <Volume2 className="w-4 h-4 dark:text-gray-300 text-gray-600" />}
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                     if (audioUrl) {
                       const link = document.createElement("a");
                       link.href = audioUrl;
                       link.download = "chandas-recitation.wav";
                       link.click();
                     }
                  }}
                  className="w-10 h-10 rounded-full dark:bg-white/5 bg-black/5 flex items-center justify-center dark:hover:bg-white/10 hover:bg-black/10 transition-colors"
                >
                  <Download className="w-4 h-4 dark:text-gray-300 text-gray-600" />
                </motion.button>
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* ========================================== */}
      {/* 🔥 THE INVISIBLE AUDIO ENGINE */}
      {/* ========================================== */}
      {/* CRITICAL FIX: crossOrigin="anonymous" allows the browser's Web Audio API to "listen" to this file! */}
      {audioUrl && (
        <audio 
          ref={audioRef} 
          src={audioUrl} 
          crossOrigin="anonymous" 
          onEnded={() => {
            setPlaying(false);
            setProgress(100);
          }}
        />
      )}
    </section>
  );
}