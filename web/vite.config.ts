import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8001,
    host: true
  },
  preview: {
    port: 4173,
    host: true
  }
});
