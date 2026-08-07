"""
Análisis estructural de código Python (Bloque 15 — Code Understanding
Foundation). Solo Python, solo estructura -- clases, funciones e imports,
extraídos con el módulo `ast` de la librería estándar (parser real, no
expresiones regulares). Cero llamadas al modelo de IA en todo este
archivo, a propósito: el resumen narrativo con IA es el Bloque 17, no
esto.

Alcance deliberadamente acotado, no una limitación accidental:
- Solo funciones y clases de NIVEL DE MÓDULO. Los métodos definidos
  DENTRO de una clase quedan afuera de este bloque a propósito -- se
  extraen los nombres de las clases, pero no lo que hay adentro de cada
  una. Es una extensión futura del analizador (más AST, mismo criterio),
  no algo que el módulo `ast` no permita hacer.
- Solo Python. JS/TS queda fuera de este bloque explícitamente (no hay
  equivalente a `ast` en la librería estándar para esos lenguajes).
- Nada de esto ejecuta ni modifica código -- solo lee y analiza.

Bloque 15 no intenta ser un índice completo de código ni reemplazar un
IDE. Su objetivo es proveer contexto estructural suficiente para análisis
asistido posterior (Bloque 17 y siguientes). Si en el futuro faltan
relaciones entre símbolos, resolución de dependencias, o seguimiento de
llamadas entre funciones, no es un descuido de este bloque -- es una
decisión de alcance tomada a propósito, a resolver en un bloque aparte
si en algún momento hace falta de verdad.
"""
import ast
import os
from dataclasses import dataclass, field
from typing import List, Optional

from local_ai.project_scanner import should_skip_dir

MAX_FILE_CHARS_FOR_ANALYSIS = 200_000  # archivos absurdamente grandes se saltan, no cuelgan el escaneo
MAX_FILES_TO_ANALYZE = 300  # mismo espíritu que MAX_STRUCTURE_ENTRIES en project_scanner.py


@dataclass
class FileAnalysis:
    relative_path: str
    language: str = "python"
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    parse_error: Optional[str] = None


def analyze_python_file(file_path: str, relative_path: Optional[str] = None) -> FileAnalysis:
    """
    Analiza un archivo Python con `ast`. Nunca lanza excepción hacia
    afuera -- cualquier problema (sintaxis inválida, archivo enorme,
    error de lectura) queda registrado en `parse_error`, para que un
    archivo con problemas no frene el resto del escaneo del proyecto.
    """
    relative_path = relative_path or os.path.basename(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read(MAX_FILE_CHARS_FOR_ANALYSIS + 1)
    except OSError as exc:
        return FileAnalysis(relative_path=relative_path, parse_error=f"No se pudo leer el archivo: {exc}")

    if len(source) > MAX_FILE_CHARS_FOR_ANALYSIS:
        return FileAnalysis(relative_path=relative_path, parse_error="Archivo demasiado grande para analizar")

    try:
        tree = ast.parse(source, filename=relative_path)
    except SyntaxError as exc:
        return FileAnalysis(relative_path=relative_path, parse_error=f"Error de sintaxis: {exc}")

    classes: List[str] = []
    functions: List[str] = []
    imports: List[str] = []

    # Solo nivel de módulo (tree.body), a propósito -- ver docstring del módulo.
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)

    return FileAnalysis(relative_path=relative_path, classes=classes, functions=functions, imports=imports)


def scan_project_code(project_path: str, max_files: int = MAX_FILES_TO_ANALYZE) -> List[FileAnalysis]:
    """
    Recorre un proyecto y analiza cada archivo `.py`, reusando las mismas
    carpetas excluidas que `local_ai/project_scanner.py` (no se reinventa
    la lista). No lee ni analiza nada que no sea `.py`.
    """
    project_path = os.path.abspath(os.path.expanduser(project_path))
    if not os.path.isdir(project_path):
        return []

    results: List[FileAnalysis] = []
    count = 0

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            if count >= max_files:
                continue
            count += 1
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, project_path)
            results.append(analyze_python_file(full_path, relative_path=rel_path))

    return results
