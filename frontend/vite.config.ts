import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// ❌ REMOVED: Replit 'runtime-error-modal', 'cartographer', and 'dev-banner' plugins.
// ❌ REMOVED: process.env.PORT and process.env.BASE_PATH checks (these crash local computers).

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // We only keep the standard, open-source plugins: React and Tailwind.
  ],
  resolve: {
    alias: {
      // This allows you to import files using "@/" instead of messy paths like "../../../"
      "@": path.resolve(__dirname, "./src"),
      // ❌ REMOVED: The '@assets' alias pointing to the deleted attached_assets folder.
    },
    dedupe: ["react", "react-dom"],
  },
  // Set the root to the current directory
  root: path.resolve(__dirname),
  build: {
    outDir: path.resolve(__dirname, "dist"),
    emptyOutDir: true,
  },
  server: {
    port: 5173,         // Standard local development port
    host: "localhost",  // Forces it to run locally on your Windows machine
    open: true          // Automatically opens your web browser when you run 'npm run dev'
  }
});