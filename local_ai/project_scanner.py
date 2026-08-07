"""
Escaneo de estructura de proyectos (Bloque 14 — Project Workspace
Foundation). Distinto de local_ai/ingestion.py: acá no se lee el
contenido de cada archivo de código, solo la estructura (qué archivos y
carpetas hay) y qué tecnologías usa, por reglas -- sin modelo, sin red.

Leer el contenido de archivos de código uno por uno es "análisis de
código", el bloque siguiente de esta etapa -- no entra acá a propósito.
"""
import os
from dataclasses import dataclass
from typing import List, Optional

from local_ai.ollama_client import OllamaUnavailableError

# Carpetas que nunca conviene recorrer: dependencias, control de
# versiones, cachés -- además de las ocultas (mismo criterio que
# local_ai/ingestion.py, pero explícito acá porque node_modules/venv no
# son "ocultas" por convención de nombre.
EXCLUDED_DIR_NAMES = {"node_modules", "venv", ".venv", "__pycache__", ".git", "dist", "build", ".pytest_cache"}

MAX_STRUCTURE_ENTRIES = 300

# Archivo marcador -> tecnología. Reglas, no modelo -- mismo criterio que
# local_ai/memory_detector.py y local_ai/goal_detector.py.
_TECHNOLOGY_MARKERS = [
    ("requirements.txt", "Python"),
    ("pyproject.toml", "Python"),
    ("package.json", "Node.js/JavaScript"),
    ("tsconfig.json", "TypeScript"),
    ("Cargo.toml", "Rust"),
    ("go.mod", "Go"),
    ("pom.xml", "Java (Maven)"),
    ("build.gradle", "Java/Kotlin (Gradle)"),
    ("Gemfile", "Ruby"),
    ("composer.json", "PHP"),
    ("Dockerfile", "Docker"),
]


@dataclass
class ScanResult:
    path: str
    structure_summary: str
    technologies: Optional[str]
    entries_found: int
    truncated: bool


def should_skip_dir(dirname: str) -> bool:
    return dirname.startswith(".") or dirname in EXCLUDED_DIR_NAMES


def scan_project_structure(path: str, max_entries: int = MAX_STRUCTURE_ENTRIES) -> ScanResult:
    """
    Recorre la carpeta del proyecto y arma un listado de archivos/carpetas
    en texto plano -- nunca lee el contenido de archivos de código. No
    modifica nada en el disco.
    """
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(path):
        return ScanResult(path=path, structure_summary="", technologies=None, entries_found=0, truncated=False)

    lines: List[str] = []
    all_filenames: List[str] = []
    entries_found = 0
    truncated = False

    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        rel_dir = os.path.relpath(dirpath, path)
        for filename in sorted(filenames):
            entries_found += 1
            all_filenames.append(filename)
            if len(lines) >= max_entries:
                truncated = True
                continue
            rel_path = filename if rel_dir == "." else os.path.join(rel_dir, filename)
            lines.append(rel_path)

    if truncated:
        lines.append(f"... ({entries_found - len(lines)} archivos más, no listados)")

    technologies = detect_technologies(all_filenames)

    return ScanResult(
        path=path,
        structure_summary="\n".join(lines) if lines else "(carpeta vacía o sin archivos legibles)",
        technologies=technologies,
        entries_found=entries_found,
        truncated=truncated,
    )


def detect_technologies(filenames: List[str]) -> Optional[str]:
    """Detecta tecnologías por presencia de archivos marcadores conocidos -- reglas, no modelo."""
    filenames_lower = {f.lower() for f in filenames}
    found = []
    for marker, technology in _TECHNOLOGY_MARKERS:
        if marker.lower() in filenames_lower and technology not in found:
            found.append(technology)
    if any(f.endswith(".py") for f in filenames_lower) and "Python" not in found:
        found.append("Python")
    if any(f.endswith((".ts", ".tsx")) for f in filenames_lower) and "TypeScript" not in found:
        found.append("TypeScript")
    if any(f.endswith((".js", ".jsx")) for f in filenames_lower) and "Node.js/JavaScript" not in found and "TypeScript" not in found:
        found.append("Node.js/JavaScript")
    return ", ".join(found) if found else None


# ----------------------------------------------------------------
# status_summary -- única parte que puede tocar el modelo, y solo bajo
# demanda (nunca automático al escanear).
# ----------------------------------------------------------------
MAX_README_CHARS = 3000

_PROJECT_SUMMARY_SYSTEM_PROMPT = (
    "Tenés la estructura de archivos de un proyecto de programación, y "
    "posiblemente el contenido de su README. Generá un resumen breve (2 a "
    "4 oraciones) de qué parece ser el proyecto y su objetivo probable. Si "
    "no hay información suficiente para saberlo, decilo honestamente en "
    "vez de inventar un objetivo."
)


def read_readme(path: str) -> Optional[str]:
    """Lee el README del proyecto si existe, sin tocar nada más. No lee ningún otro archivo de código."""
    for name in ("README.md", "README.txt", "README", "readme.md"):
        candidate = os.path.join(path, name)
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()[:MAX_README_CHARS]
            except OSError:
                return None
    return None


def generate_status_summary(structure_summary: str, ollama, readme_content: Optional[str] = None) -> Optional[str]:
    """
    Genera un resumen narrativo del proyecto con el modelo local, bajo
    demanda -- nunca se llama automáticamente desde scan_project_structure().
    Devuelve None si no hay modelo disponible o algo falla (degradación
    con gracia, mismo criterio de todo el proyecto).
    """
    if not ollama.ensure_running():
        return None

    context_chunks = [structure_summary]
    if readme_content:
        context_chunks.append(readme_content)

    try:
        answer = ollama.generate(prompt="Resumí este proyecto.", system=_PROJECT_SUMMARY_SYSTEM_PROMPT, context_chunks=context_chunks)
    except OllamaUnavailableError:
        return None

    return answer.strip() if answer and answer.strip() else None
