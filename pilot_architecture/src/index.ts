import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { appConfig } from "./lib/config.js";
import { logger } from "./lib/logger.js";
import { healthRoute } from "./routes/health.js";
import { chatRoute } from "./routes/chat.js";

const app = new Hono();

app.route("/", healthRoute);
app.route("/", chatRoute);

serve({ fetch: app.fetch, port: appConfig.port }, (info) => {
  logger.info(`Pilot architecture server running on http://localhost:${info.port}`);
});
