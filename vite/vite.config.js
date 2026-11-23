import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default {
  server: {
    port: 3000,
    strictPort: true,
    proxy: { "/api": "http://localhost:8080" }
  },

  resolve: {
    alias: {
      '@': '/src',
    }
  },

  plugins: [react(), tailwindcss()],
};
