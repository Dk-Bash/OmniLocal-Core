"""
Propuestas de cambios (Bloque 20). Primera vez que el sistema piensa
sobre TODO un proyecto, no un archivo puntual -- pero sigue sin escribir
ni ejecutar nada. Usa la ESTRUCTURA ya guardada (Bloque 15:
clases/funciones/imports por archivo), no el contenido completo de cada
archivo -- mandar todo el código de un proyecto entero no entra en un
prompt razonable.

Lenguaje del prompt deliberadamente sugerente, no prescriptivo ("podrían
estar relacionados", no "hay que modificar") -- las propuestas se basan
solo en estructura, no en código real, así que hablar con certeza sería
engañoso.
"""
import json
import re
from typing import Optional

_PROPOSAL_PATTERNS = [
    re.compile(r"\bquiero agregar (.+)", re.IGNORECASE),
    re.compile(r"\bnecesito agregar (.+)", re.IGNORECASE),
    re.compile(r"\bc[oó]mo implemento (.+)", re.IGNORECASE),
    re.compile(r"\bpropon[eé]me? cambios para (.+)", re.IGNORECASE),
]

_PROPOSAL_SYSTEM_PROMPT = (
    "Tenés la estructura de un proyecto (archivos, clases, funciones, "
    "imports) y un pedido de funcionalidad nueva. Proponé qué archivos "
    "podrían estar relacionados y qué componentes podrían ser necesarios, "
    "y un plan de alto nivel en prosa. NO escribas el código final, NO "
    "generes un diff, NO apliques nada -- esto es una propuesta para que "
    "el usuario evalúe, no una ejecución. Esta propuesta se basa solo en "
    "la estructura del proyecto, no en el código real -- puede estar "
    "incompleta o equivocada en detalles."
)


def detect_change_proposal_request(text: str) -> Optional[str]:
    """Devuelve la descripción de la funcionalidad pedida si el mensaje la matchea. None si no matchea nada."""
    text = (text or "").strip()
    if not text:
        return None
    for pattern in _PROPOSAL_PATTERNS:
        match = pattern.search(text)
        if match:
            description = match.group(1).strip().rstrip(".!¿? ")
            if description:
                return description
    return None


def build_project_overview(project, project_files: list) -> str:
    """
    Arma un resumen ESTRUCTURAL del proyecto entero (todos los archivos,
    sus clases/funciones/imports) -- no el contenido de cada uno.
    """
    lines = [f"Proyecto: {project.name}"]
    if project.technologies:
        lines.append(f"Tecnologías: {project.technologies}")
    lines.append("Archivos:")

    for pf in project_files:
        try:
            classes = json.loads(pf.get("classes") or "[]")
            functions = json.loads(pf.get("functions") or "[]")
            imports = json.loads(pf.get("imports") or "[]")
        except (ValueError, TypeError):
            classes, functions, imports = [], [], []
        lines.append(f"  - {pf['relative_path']}: clases={classes} funciones={functions} imports={imports}")

    return "\n".join(lines)
