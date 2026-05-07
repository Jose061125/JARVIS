import { Hono } from "hono";
import { z } from "zod";
import { askJarvis } from "../brain.js";
import { addTurn } from "../lib/memory.js";
import { appConfig } from "../lib/config.js";

const bodySchema = z.object({
  sessionId: z.string().min(1),
  channel: z.enum(["terminal", "web", "voice", "telegram"]).default("web"),
  message: z.string().min(1)
});

export const chatRoute = new Hono();

chatRoute.post("/api/chat", async (c) => {
  const authHeader = c.req.header("authorization") ?? "";
  const expected = `Bearer ${appConfig.triggerSecret}`;

  if (authHeader !== expected) {
    return c.json({ ok: false, error: "unauthorized" }, 401);
  }

  const raw = await c.req.json().catch(() => null);
  const parsed = bodySchema.safeParse(raw);
  if (!parsed.success) {
    return c.json({ ok: false, error: "invalid_body", details: parsed.error.flatten() }, 400);
  }

  const userTurn = {
    role: "user" as const,
    content: parsed.data.message,
    at: new Date().toISOString()
  };

  addTurn(parsed.data.sessionId, userTurn);

  const reply = await askJarvis(parsed.data);

  addTurn(parsed.data.sessionId, {
    role: "assistant",
    content: reply,
    at: new Date().toISOString()
  });

  return c.json({
    ok: true,
    sessionId: parsed.data.sessionId,
    channel: parsed.data.channel,
    reply
  });
});
