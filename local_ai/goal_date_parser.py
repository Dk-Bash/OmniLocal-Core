"""
Parser de fechas relativas por reglas (Bloque 10 — Goal Understanding &
Management). Sin modelo, sin red — instantáneo, igual criterio que
memory_detector.py y goal_detector.py.

Regla acordada para nombres de día de semana: SIEMPRE se refiere a la
próxima ocurrencia futura, nunca a "hoy" — "el lunes" dicho un lunes
significa el lunes que viene (+7 días), no hoy. "el martes" dicho un lunes
significa mañana.
"""
import re
from datetime import date, timedelta
from typing import Optional, Tuple

_WEEKDAYS = {
    "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6,
}

# Orden importa: "pasado mañana" debe revisarse antes que "mañana" sola
# (si no, "mañana" matchearía primero adentro de la frase más larga).
_PASADO_MANANA_RE = re.compile(r"\bpasado\s+mañana\b", re.IGNORECASE)
_EN_N_DIAS_RE = re.compile(r"\ben\s+(\d+)\s+d[ií]as?\b", re.IGNORECASE)
_MANANA_RE = re.compile(r"\bmañana\b", re.IGNORECASE)
_HOY_RE = re.compile(r"\bhoy\b", re.IGNORECASE)
_WEEKDAY_RE = re.compile(
    r"\b(?:el\s+)?(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b",
    re.IGNORECASE,
)


def parse_relative_date(text: str, reference_date: Optional[date] = None) -> Tuple[Optional[date], str]:
    """
    Busca una expresión de fecha relativa conocida en `text` (hoy, mañana,
    pasado mañana, "en N días", día de semana). Devuelve una tupla
    (fecha_encontrada_o_None, texto_sin_la_frase_de_fecha) -- lo segundo
    es necesario para no dejar basura tipo "Estudiar Linux mañana" como
    título de un objetivo.
    """
    reference_date = reference_date or date.today()
    text = text or ""

    match = _PASADO_MANANA_RE.search(text)
    if match:
        return reference_date + timedelta(days=2), _strip(text, match)

    match = _EN_N_DIAS_RE.search(text)
    if match:
        n = int(match.group(1))
        return reference_date + timedelta(days=n), _strip(text, match)

    match = _MANANA_RE.search(text)
    if match:
        return reference_date + timedelta(days=1), _strip(text, match)

    match = _HOY_RE.search(text)
    if match:
        return reference_date, _strip(text, match)

    match = _WEEKDAY_RE.search(text)
    if match:
        day_name = match.group(1).lower()
        target_idx = _WEEKDAYS[day_name]
        days_ahead = (target_idx - reference_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # nunca "hoy": siempre la próxima ocurrencia futura
        return reference_date + timedelta(days=days_ahead), _strip(text, match)

    return None, text.strip()


def _strip(text: str, match: "re.Match") -> str:
    cleaned = (text[: match.start()] + text[match.end():])
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,.")
    return cleaned
