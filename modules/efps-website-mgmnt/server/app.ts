/**
 * server/app.ts
 *
 * PURPOSE: Express app exposing the EasyFind Formatter API.
 * Shared between the Vite dev middleware and the production server
 * so the formatter's Gemini/Google Places calls always run server-side.
 */

import express, { type Express } from "express";
import { formatPropertyHandler, healthCheck } from "../formatter/api/formatter.handler";

export function createApiApp(): Express {
  const app = express();

  app.use(express.json({ limit: "1mb" }));

  app.post("/api/formatter", (req, res) => {
    void formatPropertyHandler({ body: req.body }, res);
  });

  app.get("/api/formatter/health", (req, res) => {
    void healthCheck(req, res);
  });

  return app;
}
