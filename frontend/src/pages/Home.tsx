// ==========================================
// IMPORTS
// ==========================================
// useRef lets us "point" to specific parts of the screen so we can scroll to them.
// useState lets React remember data (like the analyzed text) so the screen can update.
import { useRef, useState } from "react";

// Importing all the UI sections (components) we built in the other files
import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import VerseInputSection from "@/components/VerseInputSection";
import MelodySection from "@/components/MelodySection";
import AudioSection from "@/components/AudioSection";
import PipelineSection from "@/components/PipelineSection";
import FooterSection from "@/components/FooterSection";

export default function Home() {
  // ==========================================
  // STATE: REMEMBERING THE DATA
  // ==========================================
  // This state holds the result from our Python API. 
  // Initially, it is 'null' because the user hasn't analyzed anything yet.
  const [analysisResult, setAnalysisResult] = useState<null | {
    syllables: Array<{ text: string; type: "L" | "G" }>;
    metre: string;
    verse: string;
  }>(null);

  // ==========================================
  // REFS: SCROLLING TARGETS
  // ==========================================
  // We create these "Refs" to attach to the different sections of the website.
  // Think of them as anchors. When a user clicks a button in the Navbar, 
  // the code will find the matching anchor and scroll the screen down to it.
  const inputRef = useRef<HTMLDivElement>(null);
  const analysisRef = useRef<HTMLDivElement>(null);
  const melodyRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLDivElement>(null);
  const pipelineRef = useRef<HTMLDivElement>(null);

  // A helper function that takes a "Ref" (anchor) and smoothly scrolls the browser to it.
  const scrollTo = (ref: React.RefObject<HTMLDivElement | null>) => {
    ref.current?.scrollIntoView({ behavior: "smooth" });
  };

  // ==========================================
  // UI RENDER (WHAT THE USER SEES)
  // ==========================================
  return (
    // The main wrapper for the whole page. Handles the dark background color.
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      
      {/* 1. NAVBAR */}
      {/* We pass the scrollTo functions into the Navbar so its buttons work. */}
      <Navbar
        onHome={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        onInput={() => scrollTo(inputRef)}
        onMelody={() => scrollTo(melodyRef)}
        onAudio={() => scrollTo(audioRef)}
        onPipeline={() => scrollTo(pipelineRef)}
      />

      {/* 2. HERO SECTION (The Big Title) */}
      <HeroSection onAnalyze={() => scrollTo(inputRef)} onExplore={() => scrollTo(pipelineRef)} />
      
      {/* 3. INPUT SECTION (The Text Box) */}
      <div ref={inputRef}>
        <VerseInputSection
          onAnalysisComplete={(result) => {
            // When Python finishes analyzing, save the data into our State
            setAnalysisResult(result);
            // Wait 100 milliseconds, then automatically scroll down to show the results
            setTimeout(() => scrollTo(analysisRef), 100);
          }}
        />
      </div>

      {/* 4. RESULTS SECTION (Melody & Audio) */}
      <div ref={analysisRef}>
        {/* IF WE HAVE DATA: Show the real charts and the real audio player */}
        {analysisResult && (
          <>
            <div ref={melodyRef}>
              <MelodySection syllables={analysisResult.syllables} metre={analysisResult.metre} />
            </div>
            <div ref={audioRef}>
              {/* Pass the saved verse text and syllables down to the AudioSection */}
              <AudioSection syllables={analysisResult.syllables} verse={analysisResult.verse} />
            </div>
          </>
        )}
        
        {/* IF WE DO NOT HAVE DATA YET: Show empty/placeholder charts */}
        {!analysisResult && (
          <>
            <div ref={melodyRef}>
              <MelodySection syllables={[]} metre="" />
            </div>
            <div ref={audioRef}>
              {/* We pass an empty string to keep TypeScript happy before the user types anything */}
              <AudioSection syllables={[]} verse="" />
            </div>
          </>
        )}
      </div>

      {/* 5. ARCHITECTURE PIPELINE */}
      <div ref={pipelineRef}>
        <PipelineSection />
      </div>

      {/* 6. FOOTER */}
      <FooterSection onInput={() => scrollTo(inputRef)} />
    </div>
  );
}