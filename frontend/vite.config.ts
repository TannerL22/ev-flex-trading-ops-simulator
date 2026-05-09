import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/ev-flex-trading-ops-simulator/",
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173
  }
});
