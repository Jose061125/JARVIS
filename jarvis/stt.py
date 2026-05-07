"""
Módulo de reconocimiento de voz usando SpeechRecognition + Google STT (gratis).
"""

import speech_recognition as sr
from jarvis.config import SPEECH_LANG


_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 300
_recognizer.dynamic_energy_threshold = True


def listen(timeout: int = 5, phrase_limit: int = 10) -> str | None:
    """
    Escucha el micrófono y retorna el texto reconocido.
    Retorna None si no se entendió nada o hubo un error.
    """
    with sr.Microphone() as source:
        _recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return None

    try:
        text = _recognizer.recognize_google(audio, language=SPEECH_LANG)
        return text.strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None
