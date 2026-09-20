/**
 * server/index.ts
 *
 * PURPOSE: Production entry point.
 * Serves the built SPA (dist/) and the formatter API from a single
 * Node process, so secrets (Gemini, Google Places) never reach the browser.
 */

import path from "node:path";
import { fileURLToPath } from "node:url";
import express from "express";
import { createApiApp } from "./app";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distPath = path.join(__dirname, "..", "dist");

const app = createApiApp();

app.use(express.static(distPath));

// SPA fallback: any non-API route serves index.html so client-side routing works.
app.use((req, res, next) => {
  if (req.path.startsWith("/api/")) return next();
  res.sendFile(path.join(distPath, "index.html"), (err) => {
    if (err) next(err);
  });
});

const port = Number(process.env.PORT) || 3000;

app.listen(port, "0.0.0.0", () => {
  console.log(`EasyFind server listening on port ${port}`);
});
