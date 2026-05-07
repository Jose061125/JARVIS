"""
Módulo de síntesis de voz usando edge-tts (voces de Microsoft).
"""

import asyncio
import threading
import os
import tempfile

import edge_tts
import pygame

from jarvis.settings import get_setting


def speak(text: str) -> None:
    """Convierte texto a voz y lo reproduce. Bloquea hasta terminar."""
    asyncio.run(_speak_async(text))


async def _speak_async(text: str) -> None:
    tts_voice = str(get_setting("tts_voice") or "es-ES-AlvaroNeural")
    tts_rate = str(get_setting("tts_rate") or "+0%")
    communicate = edge_tts.Communicate(text, tts_voice, rate=tts_rate)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        await communicate.save(tmp_path)
        _play_audio(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _play_audio(path: str) -> None:
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit()


def speak_async(text: str) -> threading.Thread:
    """Reproduce voz en un hilo separado para no bloquear la UI."""
    t = threading.Thread(target=speak, args=(text,), daemon=True)
    t.start()
    return t
