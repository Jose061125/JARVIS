# ============================================================
#  JARVIS - Configuración
# ============================================================

import os
from pathlib import Path

# Cargar .env si existe (para desarrollo local)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# Obtén tu API key gratis en: https://console.groq.com
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "TU_API_KEY_AQUI")

# Modelo a usar (llama-3.3-70b-versatile es el más potente gratis)
GROQ_MODEL = "llama-3.3-70b-versatile"

# Voz de JARVIS (edge-tts)
# Opciones en español: es-ES-AlvaroNeural (hombre), es-ES-ElviraNeural (mujer)
# Opciones en inglés: en-US-GuyNeural, en-GB-RyanNeural
TTS_VOICE = "es-ES-AlvaroNeural"
TTS_RATE = "+0%"   # Velocidad: -20% más lento, +20% más rápido

# Nombre del asistente
ASSISTANT_NAME = "JARVIS"

# Idioma para reconocimiento de voz ("es-ES" o "en-US")
SPEECH_LANG = "es-ES"

# Palabras de activación para modo manos libres
WAKE_WORDS_RAW = os.environ.get("WAKE_WORDS", "jarvis,hey jarvis,ok jarvis")
WAKE_WORDS = [w.strip().lower() for w in WAKE_WORDS_RAW.split(",") if w.strip()]

# Personalidad del asistente (system prompt)
SYSTEM_PROMPT = f"""Eres {ASSISTANT_NAME}, un asistente de IA personal para el PC del usuario.
Eres inteligente, conciso y útil. Respondes en el mismo idioma que el usuario.
Cuando el usuario pida abrir una aplicación, responde SOLO con: OPEN_APP:<nombre_app>
Cuando el usuario pida buscar algo en internet, responde SOLO con: WEB_SEARCH:<consulta>
Cuando el usuario pida subir/bajar el volumen, responde SOLO con: VOLUME:<up|down|mute>
Cuando el usuario pida apagar el PC, responde SOLO con: POWER:shutdown
Cuando el usuario pida reiniciar el PC, responde SOLO con: POWER:restart
Cuando el usuario pida suspender o modo reposo, responde SOLO con: POWER:sleep
Cuando el usuario pida bloquear la pantalla, responde SOLO con: POWER:lock
Cuando el usuario pida desbloquear la pantalla, responde SOLO con: POWER:unlock
Cuando el usuario quiera cancelar el apagado, responde SOLO con: POWER:cancel_shutdown
Para el resto de preguntas, responde de forma natural y concisa."""
