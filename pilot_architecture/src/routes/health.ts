import { Hono } from "hono";
import { appConfig } from "../lib/config.js";

export const healthRoute = new Hono();

healthRoute.get("/health", (c) => {
  return c.json({
    ok: true,
    service: "jarvis-pilot-architecture",
    assistant: appConfig.assistantName,
    timestamp: new Date().toISOString()
  });
});
