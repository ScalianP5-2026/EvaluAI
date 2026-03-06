import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/evaluai/",
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    allowedHosts: ["ignacio.software"],
  },
});
