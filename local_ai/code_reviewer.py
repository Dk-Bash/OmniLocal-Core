"""
Revisión de código asistida (Bloque 18 — Code Review asistido). Sigue
siendo solo lectura -- nada de edición, ejecución, ni aplicación
automática de cambios. La diferencia con el Bloque 17 (Code Explanation):
acá SÍ se le pide al modelo que opine sobre calidad/diseño, en vez de
prohibírselo.

Reutiliza directamente `find_matching_project_file()` y
`read_file_content()` de local_ai/code_explainer.py -- la mecánica de
"encontrar y leer el archivo del proyecto activo" ya existe, no se
reimplementa acá.
"""
import re
from typing import Optional

from local_ai.code_explainer import find_matching_project_file, read_file_content  # noqa: F401 (reexport para quien use este módulo)

_REVIEW_PATTERNS = [
    re.compile(r"\brevis[aá](?:me|r)? (\S+\.\w+)", re.IGNORECASE),
    re.compile(r"\banaliz[aá](?:me|r)? (\S+\.\w+)", re.IGNORECASE),  # movido desde Bloque 17
    re.compile(r"\best[aá] bien(?: dise[ñn]ado| escrito)? (\S+\.\w+)", re.IGNORECASE),
    re.compile(r"\bqu[eé] opin[aá]s? de (\S+\.\w+)", re.IGNORECASE),
    re.compile(r"\bhay problemas en (\S+\.\w+)", re.IGNORECASE),
]

_REVIEW_SYSTEM_PROMPT = (
    "Revisá este archivo de código: evaluá su diseño, señalá posibles "
    "problemas, riesgos o mejoras, y explicá por qué. Podés sugerir "
    "cambios concretos como texto (ejemplos, ideas) -- pero NO los "
    "apliques, NO modificás nada, esto es una opinión, no una acción. Sé "
    "honesto: esto es una primera revisión automatizada con un modelo "
    "chico, no un reemplazo de una revisión humana ni de una herramienta "
    "de análisis estática real."
)


def detect_review_request(text: str) -> Optional[str]:
    """Devuelve el nombre de archivo mencionado si el mensaje pide revisarlo/opinar. None si no matchea nada."""
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _REVIEW_PATTERNS:
        match = pattern.search(text)
        if match:
            filename = match.group(1).strip().rstrip(".!¿? ")
            if filename:
                return filename
    return None
