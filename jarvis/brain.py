"""
Módulo de comunicación con Groq API.
"""

from groq import Groq
from jarvis.config import GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT


_client = Groq(api_key=GROQ_API_KEY)

# Historial de conversación (memoria de contexto)
_history: list[dict] = []
MAX_HISTORY = 20  # mensajes máximos en memoria


def chat(user_message: str) -> str:
    """Envía un mensaje a Groq y retorna la respuesta del LLM."""
    global _history

    _history.append({"role": "user", "content": user_message})

    # Limitar historial para no exceder tokens
    if len(_history) > MAX_HISTORY:
        _history = _history[-MAX_HISTORY:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + _history

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )

    reply = response.choices[0].message.content.strip()
    _history.append({"role": "assistant", "content": reply})
    return reply


def clear_history() -> None:
    """Limpia el historial de conversación."""
    global _history
    _history = []
