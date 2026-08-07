"""
Detección de objetivos/recordatorios en el chat (Bloque 9 — Foundation;
Bloque 10 — Understanding & Management). Módulo separado de
local_ai/memory_detector.py a propósito: son intenciones distintas
(guardar un dato sobre el usuario vs. pedir que se recuerde hacer algo),
y mantenerlos separados evita que un cambio acá interfiera con las reglas
de memoria ya probadas.

Solo reglas, sin modelo -- mismo criterio en todo el proyecto: barato,
instantáneo, sin red.

Bloque 10 agrega:
- Creación estructurada: separa la frase de fecha (vía goal_date_parser)
  del título, en vez de guardar el texto crudo tal cual.
- Detección de actualización ("cambiar X para Y" / "mover X para Y"),
  set de patrones totalmente separado de los de creación.
- find_matching_pending_goal: busca, por superposición de palabras clave
  (reutiliza retrieval.textutils.extract_keywords, sin reimplementar
  nada), un único objetivo pendiente que coincida con lo que el usuario
  mencionó. Si hay cero o más de un candidato, no adivina -- devuelve
  None para que el asistente pida aclaración.
"""
import re
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from local_ai.memory_detector import looks_like_question
from local_ai.goal_date_parser import parse_relative_date
from retrieval.textutils import extract_keywords

_CREATE_PATTERNS = [
    re.compile(r"\brecordame (?:que )?(.{2,200})", re.IGNORECASE),
    re.compile(r"\bacordate de (.{2,200})", re.IGNORECASE),
    re.compile(r"\bno te olvides de (.{2,200})", re.IGNORECASE),
]

# Set separado de los de creación, a propósito -- una intención distinta.
_UPDATE_PATTERNS = [
    re.compile(r"\bcambiar\s+(.+?)\s+para\s+(.+)", re.IGNORECASE),
    re.compile(r"\bmover\s+(.+?)\s+para\s+(.+)", re.IGNORECASE),
]


@dataclass
class GoalCandidate:
    title: str
    due_at: Optional[date] = None
    goal_type: str = "task"
    category: Optional[str] = None  # sin inferencia todavía (Bloque 10, decisión explícita)


@dataclass
class GoalUpdateCandidate:
    reference_text: str  # lo que el usuario mencionó, para buscar el objetivo existente
    new_due_at: Optional[date] = None


def detect_goal_creation(text: str) -> Optional[GoalCandidate]:
    """
    Reconoce una intención de CREAR un objetivo nuevo ("recordame que...",
    "acordate de...", "no te olvides de..."). Extrae la fecha relativa si
    hay una, dejando el título limpio (sin la frase de fecha).
    """
    text = (text or "").strip()
    if not text or looks_like_question(text):
        return None

    for pattern in _CREATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(1).strip().rstrip(".!¿? ")
        if not raw:
            continue
        due_at, title = parse_relative_date(raw)
        title = title.rstrip(".!¿? ").strip()
        if not title:
            title = raw  # si limpiar la fecha dejó el título vacío, mejor conservar el texto original
        return GoalCandidate(title=title, due_at=due_at)

    return None


def detect_goal_update(text: str) -> Optional[GoalUpdateCandidate]:
    """
    Reconoce una intención de MODIFICAR un objetivo existente ("cambiar X
    para Y", "mover X para Y"). Requiere mención explícita de a qué
    objetivo se refiere -- "cambialo para el viernes" sin nombrar nada no
    matchea ningún patrón acá, queda fuera de alcance a propósito.
    """
    text = (text or "").strip()
    if not text or looks_like_question(text):
        return None

    for pattern in _UPDATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        reference_text = match.group(1).strip()
        date_phrase = match.group(2).strip()
        if not reference_text:
            continue
        new_due_at, _ = parse_relative_date(date_phrase)
        return GoalUpdateCandidate(reference_text=reference_text, new_due_at=new_due_at)

    return None


def find_matching_pending_goal(pending_goals: List, reference_text: str):
    """
    Busca, entre los objetivos pendientes (nunca completados/cancelados --
    eso lo garantiza quien arma `pending_goals`), cuál coincide con
    `reference_text` por superposición de palabras clave. Devuelve el Goal
    si hay EXACTAMENTE un candidato con al menos una palabra clave en
    común; None si no hay ninguno o si hay más de uno (ambiguo -- nunca
    se adivina cuál).
    """
    keywords = set(extract_keywords(reference_text))
    if not keywords:
        return None

    matches = []
    for goal in pending_goals:
        goal_keywords = set(extract_keywords(goal.content))
        if keywords & goal_keywords:
            matches.append(goal)

    if len(matches) == 1:
        return matches[0]
    return None
