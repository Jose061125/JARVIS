"""
Módulo de reconocimiento de voz usando SpeechRecognition + Google STT (gratis).
"""

import speech_recognition as sr
from jarvis.settings import get_setting


_recognizer = sr.Recognizer()
_recognizer.energy_threshold = 300
_recognizer.dynamic_energy_threshold = True


def listen_with_audio(timeout: int = 5, phrase_limit: int = 10) -> tuple[str | None, sr.AudioData | None]:
    """
    Escucha el micrófono y retorna una tupla (texto, audio).
    Si no se pudo transcribir, texto sera None pero audio puede existir.
    """
    with sr.Microphone() as source:
        _recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return None, None

    try:
        speech_lang = str(get_setting("speech_lang") or "es-ES")
        text = _recognizer.recognize_google(audio, language=speech_lang)
        return text.strip(), audio
    except sr.UnknownValueError:
        return None, audio
    except sr.RequestError:
        return None, audio


def listen(timeout: int = 5, phrase_limit: int = 10) -> str | None:
    """
    Escucha el micrófono y retorna el texto reconocido.
    Retorna None si no se entendió nada o hubo un error.
    """
    text, _audio = listen_with_audio(timeout=timeout, phrase_limit=phrase_limit)
    return text
