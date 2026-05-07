"""
Verificacion de voz ligera para el modo wake.
No es biometria de grado seguridad, solo una validacion basica.
"""

from __future__ import annotations

import audioop
import math
from typing import Sequence

import speech_recognition as sr


def _resample_signature(values: list[float], target_len: int = 20) -> list[float]:
    if target_len <= 0:
        return []
    if not values:
        return [0.0] * target_len
    if len(values) == target_len:
        return values

    out: list[float] = []
    max_idx = len(values) - 1
    for i in range(target_len):
        pos = (i * max_idx) / max(1, target_len - 1)
        lo = int(math.floor(pos))
        hi = min(max_idx, lo + 1)
        frac = pos - lo
        interp = values[lo] * (1.0 - frac) + values[hi] * frac
        out.append(interp)
    return out


def extract_voice_signature(audio: sr.AudioData) -> list[float]:
    """Extrae una firma numerica de amplitud temporal normalizada."""
    raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
    if not raw:
        return []

    chunk_size = 800
    rms_values: list[float] = []

    for i in range(0, len(raw), chunk_size):
        chunk = raw[i:i + chunk_size]
        if len(chunk) < 200:
            continue
        rms_values.append(float(audioop.rms(chunk, 2)))

    if not rms_values:
        return []

    max_rms = max(rms_values) or 1.0
    normalized = [min(1.0, max(0.0, v / max_rms)) for v in rms_values]
    return _resample_signature(normalized, target_len=20)


def similarity_score(sig_a: Sequence[float], sig_b: Sequence[float]) -> float:
    """Retorna un score [0,1] donde 1 significa muy similar."""
    if not sig_a or not sig_b:
        return 0.0

    n = min(len(sig_a), len(sig_b))
    if n == 0:
        return 0.0

    diffs = [abs(float(sig_a[i]) - float(sig_b[i])) for i in range(n)]
    mean_diff = sum(diffs) / n
    return max(0.0, min(1.0, 1.0 - mean_diff))


def verify_voice(audio: sr.AudioData, reference_signature: Sequence[float], threshold: float = 0.72) -> tuple[bool, float]:
    """Compara la voz actual con una firma guardada."""
    current_signature = extract_voice_signature(audio)
    if not current_signature:
        return False, 0.0

    score = similarity_score(current_signature, reference_signature)
    return score >= threshold, score
