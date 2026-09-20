/**
 * server/vite-formatter-plugin.ts
 *
 * PURPOSE: Mount the formatter API as Vite dev-server middleware so
 * `npm run dev` serves the SPA and the formatter API on the same port.
 */

import type { Plugin } from "vite";
import { createApiApp } from "./app";

export function formatterApiPlugin(): Plugin {
  return {
    name: "easyfind-formatter-api",
    configureServer(server) {
      server.middlewares.use(createApiApp());
    },
  };
}
