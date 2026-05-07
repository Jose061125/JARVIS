import type { ChatTurn } from "../types/chat.js";

type SessionStore = Map<string, ChatTurn[]>;

const store: SessionStore = new Map();
const MAX_TURNS = 10;

export function addTurn(sessionId: string, turn: ChatTurn): void {
  const turns = store.get(sessionId) ?? [];
  turns.push(turn);
  if (turns.length > MAX_TURNS) {
    turns.splice(0, turns.length - MAX_TURNS);
  }
  store.set(sessionId, turns);
}

export function getRecentTurns(sessionId: string): ChatTurn[] {
  return store.get(sessionId) ?? [];
}
