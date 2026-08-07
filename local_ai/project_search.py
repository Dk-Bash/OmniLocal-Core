"""
Exploración segura de proyectos (Bloque 19). Dos capacidades
determinísticas, sin modelo:

1. Búsqueda de contenido -- en vivo, sin índice persistente (mismo motivo
   que el Bloque 15 nunca guardó contenido completo: evitar una base que
   crece sin límite y queda desactualizada). Coincidencia LITERAL de
   texto, sin inferencia semántica -- eso queda fuera a propósito.
2. Relaciones por imports -- consulta estructural sobre `project_files`
   (Bloque 15), sin volver a tocar el disco.

Reusa las mismas exclusiones de carpetas que el resto del proyecto
(`should_skip_dir`, Bloque 14) -- no una lista nueva.
"""
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from local_ai.project_scanner import should_skip_dir

# Extensiones de texto reconocidas -- mismo espíritu que local_ai/ingestion.py,
# ampliado para código y archivos de configuración comunes.
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".markdown",
    ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".html", ".css",
    ".sql", ".sh", ".env", ".rst",
}

BINARY_CHECK_BYTES = 1024
MAX_FILE_CHARS_PER_SEARCH = 200_000  # mismo orden que MAX_FILE_CHARS_FOR_ANALYSIS (Bloque 15)
MAX_FILES_TO_SEARCH = 300  # mismo límite de cantidad que el resto del proyecto
DEFAULT_MAX_MATCHES = 20


@dataclass
class SearchMatch:
    relative_path: str
    line_number: int
    snippet: str


def is_probably_binary(file_path: str) -> bool:
    """
    Chequeo barato y estándar: si aparece un byte nulo en los primeros
    BINARY_CHECK_BYTES bytes, se asume binario y no se intenta leer como
    texto. No es 100% infalible, pero evita el caso común (imágenes,
    ejecutables, bases de datos compiladas).
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(BINARY_CHECK_BYTES)
    except OSError:
        return True  # si no se puede ni abrir, tratarlo como no-buscable
    return b"\x00" in chunk


def _has_recognized_extension(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in TEXT_EXTENSIONS or filename.lower().startswith(".env")


def search_project_content(
    project_path: str,
    term: str,
    max_matches: int = DEFAULT_MAX_MATCHES,
    max_files: int = MAX_FILES_TO_SEARCH,
) -> List[SearchMatch]:
    """
    Busca `term` como substring literal (case-insensitive), línea por
    línea, en los archivos de texto del proyecto -- sin índice, calculado
    en el momento. Reusa las mismas exclusiones de carpetas que el resto
    del proyecto. Nunca lanza excepción por un archivo individual con
    problemas (binario, error de lectura, demasiado grande) -- lo salta y
    sigue con el resto.
    """
    project_path = os.path.abspath(os.path.expanduser(project_path))
    term = (term or "").strip()
    if not term or not os.path.isdir(project_path):
        return []

    term_lower = term.lower()
    matches: List[SearchMatch] = []
    files_checked = 0

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for filename in sorted(filenames):
            if len(matches) >= max_matches or files_checked >= max_files:
                return matches
            if not _has_recognized_extension(filename):
                continue

            full_path = os.path.join(dirpath, filename)
            if is_probably_binary(full_path):
                continue

            files_checked += 1
            rel_path = os.path.relpath(full_path, project_path)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(MAX_FILE_CHARS_PER_SEARCH + 1)
            except OSError:
                continue

            if len(content) > MAX_FILE_CHARS_PER_SEARCH:
                content = content[:MAX_FILE_CHARS_PER_SEARCH]

            for line_number, line in enumerate(content.splitlines(), start=1):
                if term_lower in line.lower():
                    matches.append(SearchMatch(relative_path=rel_path, line_number=line_number, snippet=line.strip()[:200]))
                    if len(matches) >= max_matches:
                        break

    return matches


def find_files_importing(project_files: List[dict], module_name: str) -> List[dict]:
    """
    Consulta estructural: qué archivos importan `module_name`. Usa
    `project_files.imports` (ya guardado por el Bloque 15) -- no vuelve a
    leer nada del disco.
    """
    module_name = (module_name or "").strip()
    if not module_name:
        return []
    result = []
    for pf in project_files:
        try:
            imports = json.loads(pf.get("imports") or "[]")
        except (ValueError, TypeError):
            continue
        if any(module_name == imp or imp.startswith(module_name + ".") for imp in imports):
            result.append(pf)
    return result


def get_file_imports(project_files: List[dict], relative_path: str) -> Optional[List[str]]:
    """Qué importa un archivo puntual -- consulta estructural, sin tocar el disco."""
    for pf in project_files:
        if pf.get("relative_path") == relative_path:
            try:
                return json.loads(pf.get("imports") or "[]")
            except (ValueError, TypeError):
                return []
    return None


# ----------------------------------------------------------------
# Detección de intención (reglas, cero modelo) -- mismo criterio de siempre
# ----------------------------------------------------------------
_SEARCH_PATTERNS = [
    re.compile(r"\bbusc[aá](?:me|r)? (?:d[oó]nde est[aá] )?(.+)", re.IGNORECASE),
    re.compile(r"\bd[oó]nde est[aá] implementad[oa] (.+)", re.IGNORECASE),
    re.compile(r"\bencontr[aá](?:me|r)? (.+)", re.IGNORECASE),
]

_WHO_IMPORTS_PATTERNS = [
    re.compile(r"\bqu[eé] archivos importan (\S+)", re.IGNORECASE),
    re.compile(r"\bqui[eé]n importa (\S+)", re.IGNORECASE),
]

_WHAT_IMPORTS_PATTERNS = [
    re.compile(r"\bqu[eé] importa (\S+\.\w+)", re.IGNORECASE),
]


def detect_search_request(text: str) -> Optional[str]:
    """Devuelve el término a buscar si el mensaje pide explorar el proyecto. None si no matchea."""
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _SEARCH_PATTERNS:
        match = pattern.search(text)
        if match:
            term = match.group(1).strip().rstrip(".!¿? ")
            if term:
                return term
    return None


def detect_import_relation_request(text: str) -> Optional[Tuple[str, str]]:
    """
    Devuelve (tipo, valor) -- tipo es 'who_imports' (qué archivos importan
    a X) o 'what_imports' (qué importa el archivo X). None si no matchea.
    """
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _WHO_IMPORTS_PATTERNS:
        match = pattern.search(text)
        if match:
            value = match.group(1).strip().rstrip(".!¿? ")
            if value:
                return "who_imports", value
    for pattern in _WHAT_IMPORTS_PATTERNS:
        match = pattern.search(text)
        if match:
            value = match.group(1).strip().rstrip(".!¿? ")
            if value:
                return "what_imports", value
    return None
