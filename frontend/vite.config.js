import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Derive the backend proxy target from the environment.
// - Set BACKEND_PROXY_TARGET=http://localhost:8000 when running Vite outside
//   docker-compose (e.g. a local dev environment or VS Code dev container).
// - Leave unset (or set to http://backend:8000) when running inside
//   docker-compose, where the backend container is reachable by hostname.
const backendTarget = process.env.BACKEND_PROXY_TARGET || "http://backend:8000";

export default defineConfig({
  base: "/evaluai/",

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
    host: "0.0.0.0", // Expose to all network interfaces (needed for Docker/DevContainers)
    // Development server port for Vite React app
    port: 3000,
    host: true,
    allowedHosts: ["ignacio.software"],

    /**
     * Proxy configuration for development
     * Routes all /api/* requests to the backend service.
     * Target is read from BACKEND_PROXY_TARGET env var so that:
     *   - docker-compose: http://backend:8000  (default)
     *   - local / dev container: http://localhost:8000
     */
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true, // Modifies request host header to match target origin
      },
    },
  },
});
