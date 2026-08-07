"""
Explicación de código (Bloque 17 — Code Explanation / Review). Solo
lectura, solo explicación -- sin edición, sin ejecución, sin
herramientas. Usa el proyecto activo de la sesión (Bloque 16) y la
estructura ya extraída (Bloque 15); lo único nuevo acá es leer el
CONTENIDO del archivo mencionado.

Deliberadamente NO opina sobre calidad ni sugiere cambios -- eso es una
etapa aparte (revisión de código, todavía no auditada). El prompt al
modelo lo deja explícito.
"""
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional

_EXPLAIN_PATTERNS = [
    re.compile(r"\bexplic[aá](?:me|r)?(?: el archivo| el m[oó]dulo)? (\S+\.\w+)", re.IGNORECASE),
    re.compile(r"\bqu[eé] hace (\S+\.\w+)", re.IGNORECASE),
]

MAX_FILE_CHARS_FOR_EXPLANATION = 6000

_EXPLAIN_SYSTEM_PROMPT = (
    "Tenés el contenido de un archivo de código y su estructura (clases, "
    "funciones, imports). Explicá qué hace: qué contiene, para qué sirve, "
    "cómo se relaciona con lo que importa. NO opines si está bien o mal "
    "diseñado, NO sugieras cambios ni mejoras -- eso es una etapa aparte. "
    "Solo explicá qué hace, de forma clara."
)


@dataclass
class FileReadResult:
    content: Optional[str]
    truncated: bool
    error: Optional[str]


def detect_explain_request(text: str) -> Optional[str]:
    """Devuelve el nombre de archivo mencionado si el mensaje pide explicarlo. None si no matchea nada."""
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _EXPLAIN_PATTERNS:
        match = pattern.search(text)
        if match:
            filename = match.group(1).strip().rstrip(".!¿? ")
            if filename:
                return filename
    return None


def find_matching_project_file(project_files: List[dict], mentioned_filename: str) -> Optional[dict]:
    """
    Busca, entre los archivos ya indexados del proyecto activo (Bloque 15),
    cuál coincide con `mentioned_filename` -- por nombre base exacto, o por
    único candidato que termine con ese sufijo. Ambiguo o sin match -> None,
    nunca se adivina.
    """
    mentioned_filename = mentioned_filename.strip().lstrip("./\\")
    if not mentioned_filename:
        return None

    exact = [f for f in project_files if os.path.basename(f["relative_path"]) == mentioned_filename]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None  # mismo nombre en más de una carpeta -- ambiguo

    suffix_matches = [f for f in project_files if f["relative_path"].replace("\\", "/").endswith(mentioned_filename.replace("\\", "/"))]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    return None


def read_file_content(file_path: str, max_chars: int = MAX_FILE_CHARS_FOR_EXPLANATION) -> FileReadResult:
    """Lee el contenido de un archivo, solo lectura. Nunca lanza excepción -- error legible en su lugar."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars + 1)
    except OSError as exc:
        return FileReadResult(content=None, truncated=False, error=f"No se pudo leer el archivo: {exc}")

    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars]

    return FileReadResult(content=content, truncated=truncated, error=None)


def build_explanation_context(project_file: dict, file_content: str, truncated: bool) -> List[str]:
    """Arma el contexto (estructura ya conocida + contenido) para pasarle al modelo."""
    classes = json.loads(project_file["classes"]) if project_file.get("classes") else []
    functions = json.loads(project_file["functions"]) if project_file.get("functions") else []
    imports = json.loads(project_file["imports"]) if project_file.get("imports") else []

    structure_note = f"Archivo: {project_file['relative_path']}\nClases: {classes}\nFunciones: {functions}\nImports: {imports}"
    content_note = file_content
    if truncated:
        content_note += "\n... (contenido recortado por tamaño)"

    return [structure_note, content_note]
