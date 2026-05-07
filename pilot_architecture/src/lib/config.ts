import { config as loadEnv } from "dotenv";

loadEnv();

export const appConfig = {
  port: Number(process.env.PORT ?? 3141),
  triggerSecret: process.env.TRIGGER_SECRET ?? "dev-secret-change-me",
  assistantName: process.env.ASSISTANT_NAME ?? "JARVIS",
  ownerName: process.env.OWNER_NAME ?? "Owner",
  ownerRole: process.env.OWNER_ROLE ?? "Builder"
};
