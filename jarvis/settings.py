"""
Persistencia y acceso de ajustes de usuario para ECHONEX.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from jarvis import config


_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"
_LOCK = Lock()

_DEFAULTS = {
    "wake_mode_default": False,
    "wake_words": ", ".join(config.WAKE_WORDS),
    "tts_voice": "es-MX-DaliaNeural",
    "tts_rate": "-6%",
    "speech_lang": config.SPEECH_LANG,
    "groq_model": config.GROQ_MODEL,
    "response_style": "normal",
    "user_name": "Usuario",
    "announce_datetime_on_start": True,
}

_runtime_settings = dict(_DEFAULTS)


def _sanitize(raw: dict | None) -> dict:
    data = dict(_DEFAULTS)
    if not isinstance(raw, dict):
        return data

    if isinstance(raw.get("wake_mode_default"), bool):
        data["wake_mode_default"] = raw["wake_mode_default"]

    wake_words = raw.get("wake_words")
    if isinstance(wake_words, str) and wake_words.strip():
        data["wake_words"] = wake_words.strip()

    tts_voice = raw.get("tts_voice")
    if isinstance(tts_voice, str) and tts_voice.strip():
        data["tts_voice"] = tts_voice.strip()

    tts_rate = raw.get("tts_rate")
    if isinstance(tts_rate, str) and tts_rate.strip():
        data["tts_rate"] = tts_rate.strip()

    speech_lang = raw.get("speech_lang")
    if isinstance(speech_lang, str) and speech_lang.strip():
        data["speech_lang"] = speech_lang.strip()

    groq_model = raw.get("groq_model")
    if isinstance(groq_model, str) and groq_model.strip():
        data["groq_model"] = groq_model.strip()

    response_style = raw.get("response_style")
    if response_style in {"breve", "normal", "detallado"}:
        data["response_style"] = response_style

    user_name = raw.get("user_name")
    if isinstance(user_name, str) and user_name.strip():
        data["user_name"] = user_name.strip()

    announce_datetime = raw.get("announce_datetime_on_start")
    if isinstance(announce_datetime, bool):
        data["announce_datetime_on_start"] = announce_datetime

    return data


def _read_file_settings() -> dict:
    if not _SETTINGS_PATH.exists():
        return dict(_DEFAULTS)
    try:
        payload = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)
    return _sanitize(payload)


def load_settings() -> dict:
    """Carga ajustes desde disco y actualiza runtime."""
    global _runtime_settings
    with _LOCK:
        _runtime_settings = _read_file_settings()
        return dict(_runtime_settings)


def get_setting(key: str):
    """Obtiene un ajuste del runtime; si no existe, devuelve el default."""
    with _LOCK:
        if not _runtime_settings:
            _runtime_settings.update(_DEFAULTS)
        return _runtime_settings.get(key, _DEFAULTS.get(key))


def get_settings() -> dict:
    """Retorna copia de los ajustes en runtime."""
    with _LOCK:
        if not _runtime_settings:
            _runtime_settings.update(_DEFAULTS)
        return dict(_runtime_settings)


def save_settings(new_values: dict) -> dict:
    """Guarda ajustes en disco y runtime. Devuelve ajustes saneados."""
    global _runtime_settings
    with _LOCK:
        merged = dict(_runtime_settings or _DEFAULTS)
        merged.update(new_values)
        sanitized = _sanitize(merged)
        _SETTINGS_PATH.write_text(json.dumps(sanitized, indent=2, ensure_ascii=True), encoding="utf-8")
        _runtime_settings = dict(sanitized)
        return dict(_runtime_settings)


def get_wake_words() -> list[str]:
    raw = str(get_setting("wake_words") or "")
    words = [w.strip().lower() for w in raw.split(",") if w.strip()]
    return words if words else list(config.WAKE_WORDS)
