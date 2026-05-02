import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 900
  },
  server: {
    port: 5173,
    proxy: {
      "/runs": "http://127.0.0.1:8765",
      "/reference-images": "http://127.0.0.1:8765",
      "/healthz": "http://127.0.0.1:8765"
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts"
  }
});
