"""
Memoria ligera de interacciones para respuestas menos repetitivas.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
import random


_MEMORY_PATH = Path(__file__).resolve().parent.parent / "interaction_memory.json"
_LOCK = Lock()


def _default_data() -> dict:
    return {
        "stats": {},
        "recent_messages": {},
    }


def _load_data() -> dict:
    if not _MEMORY_PATH.exists():
        return _default_data()
    try:
        payload = json.loads(_MEMORY_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.setdefault("stats", {})
            payload.setdefault("recent_messages", {})
            return payload
    except (json.JSONDecodeError, OSError):
        pass
    return _default_data()


def _save_data(data: dict) -> None:
    _MEMORY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def record_request(intent: str, target: str) -> tuple[int, int]:
    """Registra la peticion y devuelve (count_target, total_intent)."""
    intent = intent.strip().lower()
    normalized_target = target.strip().lower() or "general"

    with _LOCK:
        data = _load_data()
        stats = data.setdefault("stats", {})
        intent_stats = stats.setdefault(intent, {"total": 0, "targets": {}})
        intent_stats["total"] = int(intent_stats.get("total", 0)) + 1
        targets = intent_stats.setdefault("targets", {})
        targets[normalized_target] = int(targets.get(normalized_target, 0)) + 1
        _save_data(data)
        return targets[normalized_target], intent_stats["total"]


def choose_non_repetitive(intent: str, candidates: list[str]) -> str:
    """Selecciona un mensaje evitando repetir los ultimos usados en ese intent."""
    intent = intent.strip().lower()
    if not candidates:
        return "Hecho."

    with _LOCK:
        data = _load_data()
        recent_map = data.setdefault("recent_messages", {})
        recent = recent_map.setdefault(intent, [])

        available = [c for c in candidates if c not in recent[-3:]]
        pool = available if available else candidates
        chosen = random.choice(pool)

        recent.append(chosen)
        recent_map[intent] = recent[-8:]
        _save_data(data)
        return chosen


def build_search_confirmation(query: str) -> str:
    count_target, total_intent = record_request("web_search", query)

    if count_target <= 1:
        options = [
            "Consulta hecha. Ya te deje los resultados abiertos.",
            "Busqueda completada. Tienes los resultados en el navegador.",
            "Listo, la consulta ya esta abierta.",
        ]
    elif count_target <= 4:
        options = [
            "Hecho, volvi a ejecutar esa consulta para ti.",
            "Listo, repeti la busqueda y ya esta abierta.",
            "Consulta relanzada. Revisa la pestana que acabo de abrir.",
        ]
    else:
        options = [
            "Otra vez listo. Ya deje esa consulta abierta como de costumbre.",
            "Busqueda recurrente ejecutada. Resultados abiertos.",
            "Hecho, ya sabes: consulta abierta y lista para revisar.",
        ]

    if total_intent % 7 == 0:
        options.append("Perfecto, consulta hecha. Cada vez queda mas afinado tu flujo de busqueda.")

    return choose_non_repetitive("web_search", options)


def build_site_confirmation(target: str) -> str:
    clean_target = target.strip().lower() or "sitio"
    count_target, _ = record_request("web_open", clean_target)

    if count_target <= 1:
        options = [
            "Sitio abierto. Ya puedes continuar.",
            "Listo, pagina abierta correctamente.",
            "Hecho, el sitio ya esta en pantalla.",
        ]
    elif count_target <= 4:
        options = [
            f"Listo, volvi a abrir {clean_target}.",
            f"Hecho, {clean_target} abierto otra vez.",
            f"Perfecto, ya te lleve de nuevo a {clean_target}.",
        ]
    else:
        options = [
            f"{clean_target} abierto. Ya es uno de tus accesos rapidos.",
            f"Hecho, {clean_target} listo como siempre.",
            f"Listo, acceso recurrente a {clean_target} completado.",
        ]

    return choose_non_repetitive("web_open", options)
