"""
Detección de pedidos de síntesis abierta (Bloque 11C — Personal Context
Synthesis). Reglas, un set chico y curado -- a propósito no intenta cubrir
todo lo posible, el espacio de formas de "preguntar sobre uno mismo en
general" es demasiado amplio y ambiguo para intentarlo con reglas
exhaustivas. Mejor un set preciso que uno grande con falsos positivos.

Separado de local_ai/global_context_detector.py (Bloque 11B) a propósito:
son primos funcionalmente, pero mezclar "detección de sección exacta" con
"detección de síntesis abierta" en el mismo archivo confunde más que
ayuda. Sin solapamiento intencional: frases como "en qué trabajo" quedan
fuera de acá porque ya las resuelve 11B (más rápido, sin modelo).
"""
import re

_SYNTHESIS_PATTERNS = [
    re.compile(r"\bdame un resumen\b", re.IGNORECASE),
    re.compile(r"\bqu[eé] sab[eé]s de m[ií]\b", re.IGNORECASE),
    re.compile(r"\bcosas importantes que sab[eé]s de m[ií]\b", re.IGNORECASE),
    re.compile(r"\bcu[aá]l es mi situaci[oó]n actual\b", re.IGNORECASE),
    re.compile(r"\bcontame mi situaci[oó]n\b", re.IGNORECASE),
    re.compile(r"\bresumen de mi situaci[oó]n\b", re.IGNORECASE),
]


def detect_synthesis_query(text: str) -> bool:
    """
    True si el mensaje matchea alguno de los patrones de síntesis
    conocidos. False en cualquier otro caso -- nunca se adivina; una
    frase ambigua o no prevista sigue el flujo normal (igual criterio que
    el Bloque 11B).
    """
    text = (text or "").strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _SYNTHESIS_PATTERNS)
