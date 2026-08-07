"""
Vinculación de proyecto activo a la sesión (Bloque 16 — Project Context
Binding). Solo reglas, cero modelo, cero análisis, cero ejecución.

Activación explícita únicamente -- sin inferir de qué proyecto está
hablando el usuario a partir del contenido de la charla. Mismo criterio
que `local_ai/goal_detector.py`: nunca adivinar cuando hay ambigüedad,
mejor pedir aclaración.
"""
import re
from typing import List, Optional

from retrieval.textutils import extract_keywords

_SWITCH_PATTERNS = [
    re.compile(r"\btrabajemos en (.+)", re.IGNORECASE),
    re.compile(r"\bactiv[aá] el proyecto (.+)", re.IGNORECASE),
    re.compile(r"\bcambia(?:te|r) al? proyecto (.+)", re.IGNORECASE),
]


def detect_project_switch(text: str) -> Optional[str]:
    """
    Devuelve el nombre de proyecto mencionado si el mensaje matchea un
    patrón conocido de "cambiar de contexto". None si no matchea nada --
    no se adivina intención a partir de frases no reconocidas.
    """
    text = (text or "").strip()
    if not text:
        return None

    for pattern in _SWITCH_PATTERNS:
        match = pattern.search(text)
        if match:
            mentioned = match.group(1).strip().rstrip(".!¿? ")
            if mentioned:
                return mentioned
    return None


def find_matching_project(projects: List, mentioned_text: str):
    """
    Busca, entre los proyectos registrados, cuál coincide con
    `mentioned_text` por superposición de palabras clave contra
    `project.name`. Devuelve el Project si hay EXACTAMENTE un candidato
    claro; None si no hay ninguno o hay más de uno (ambiguo -- nunca se
    adivina cuál). Mismo patrón que
    local_ai/goal_detector.py::find_matching_pending_goal (Bloque 10).
    """
    keywords = set(extract_keywords(mentioned_text))
    if not keywords:
        return None

    matches = []
    for project in projects:
        project_keywords = set(extract_keywords(project.name))
        if keywords & project_keywords:
            matches.append(project)

    if len(matches) == 1:
        return matches[0]
    return None
