import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  /**
   * envDir: "../"
   *
   * Tells Vite to load environment variables from the project root (.env)
   * instead of from ./frontend/.env. This ensures frontend and backend
   * share the same centralized .env configuration file.
   *
   * Vite will automatically inject VITE_* prefixed variables into the bundle.
   */
  envDir: "../",

  plugins: [react()],

  server: {
    // Development server port for Vite React app
    port: 5173,

    /**
     * Proxy configuration for development
     * Routes all /api/* requests to the backend service.
     * In docker-compose: routes to http://backend:8000
     * In dev container: routes to http://localhost:8000
     */
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true, // Modifies request host header to match target origin
      },
    },
  },
});
