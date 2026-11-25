import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default {
  server: {
    port: 3000,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8080" }
  },

  resolve: {
    alias: {
      '@': '/src',
    }
  },

  plugins: [react(), tailwindcss()],
};
