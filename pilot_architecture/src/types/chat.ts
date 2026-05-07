export type ChatChannel = "terminal" | "web" | "voice" | "telegram";

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
  at: string;
};
