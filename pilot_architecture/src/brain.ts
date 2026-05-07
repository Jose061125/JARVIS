import { appConfig } from "./lib/config.js";
import { getRecentTurns } from "./lib/memory.js";
import type { ChatChannel } from "./types/chat.js";

function buildPersonalityPrompt(): string {
  return [
    `Eres ${appConfig.assistantName}, asistente personal de ${appConfig.ownerName} (${appConfig.ownerRole}).`,
    "Hablas en espanol, directo y util.",
    "Da respuestas cortas y accionables.",
    "Si detectas una tarea, propone siguiente paso concreto."
  ].join(" ");
}

export async function askJarvis(input: {
  sessionId: string;
  channel: ChatChannel;
  message: string;
}): Promise<string> {
  const context = getRecentTurns(input.sessionId)
    .map((turn) => `${turn.role.toUpperCase()}: ${turn.content}`)
    .join("\\n");

  const prompt = [
    buildPersonalityPrompt(),
    `Canal: ${input.channel}.`,
    context ? `Contexto reciente:\n${context}` : "Sin contexto previo.",
    `Mensaje del usuario: ${input.message}`
  ].join("\\n\\n");

  // Piloto sin costo: respuesta heuristica local.
  // Aqui luego conectamos Claude Agent SDK en la siguiente fase.
  if (input.message.toLowerCase().includes("quien eres") || input.message.toLowerCase().includes("quién eres")) {
    return `Soy ${appConfig.assistantName}, tu copiloto personal para ejecutar, decidir y darte foco.`;
  }

  return `Modo piloto activo. Entendi: "${input.message}". Siguiente paso recomendado: convertir esto en accion concreta hoy.`;
}

export function getDebugPromptPreview(): string {
  return buildPersonalityPrompt();
}
