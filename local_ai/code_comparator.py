"""
Comparación de dos archivos (Bloque 19). A diferencia de la búsqueda y
las relaciones por imports (determinísticas), acá sí hace falta el
modelo para sintetizar la comparación. Solo lectura -- reusa
`find_matching_project_file`/`read_file_content` de
local_ai/code_explainer.py, no reimplementa nada.
"""
import re
from typing import Optional, Tuple

_COMPARE_PATTERNS = [
    re.compile(r"\bcompar[aá](?:me|r)? (\S+\.\w+) (?:y|con) (\S+\.\w+)", re.IGNORECASE),
    re.compile(r"\bdiferencia entre (\S+\.\w+) y (\S+\.\w+)", re.IGNORECASE),
]

_COMPARE_SYSTEM_PROMPT = (
    "Tenés el contenido de dos archivos de código. Compará qué hace cada "
    "uno, en qué se parecen y en qué se diferencian. NO modificás nada, "
    "esto es una comparación informativa. Sé honesto: esto es una primera "
    "comparación automatizada con un modelo chico, no un análisis "
    "exhaustivo."
)


def detect_compare_request(text: str) -> Optional[Tuple[str, str]]:
    """Devuelve (archivo_a, archivo_b) si el mensaje pide comparar dos archivos. None si no matchea."""
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _COMPARE_PATTERNS:
        match = pattern.search(text)
        if match:
            file_a = match.group(1).strip().rstrip(".!¿? ")
            file_b = match.group(2).strip().rstrip(".!¿? ")
            if file_a and file_b:
                return file_a, file_b
    return None
