import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import tailwindcss from "@tailwindcss/vite";
import { formatterApiPlugin } from "./server/vite-formatter-plugin";

export default defineConfig({
  plugins: [tailwindcss(), TanStackRouterVite(), react(), formatterApiPlugin()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5000,
    allowedHosts: true,
  },
  preview: {
    allowedHosts: true,
  },
});
