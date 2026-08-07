"""
Detección de preguntas de "vista global" (Bloque 11B — Personal Context
Awareness). Reglas, sin modelo -- mismo criterio en todo el proyecto.

Cada patrón mapea a UNA sección concreta y enumerable del digest del
Bloque 11A (nunca "todo junto") -- pendientes, proyectos, preferencias,
ocupación. Preguntas genuinamente abiertas/subjetivas ("resumen", "cosas
importantes ahora", "cómo estoy") quedan fuera a propósito: piden síntesis
real, eso es el Bloque 11C.

Regla de ambigüedad (condición de la aprobación): si el mensaje no
matchea ninguno de los patrones conocidos, no se activa nada acá -- se
sigue el flujo normal (búsqueda léxica/semántica/modelo). Nunca se
adivina la intención a partir de una frase parecida pero no reconocida.
"""
import re
from dataclasses import dataclass
from typing import Optional

_SECTION_PATTERNS = {
    "objetivos_pendientes": [
        re.compile(r"\bqu[eé] tengo pendiente", re.IGNORECASE),
        re.compile(r"\bmis pendientes\b", re.IGNORECASE),
        re.compile(r"\bqu[eé] objetivos tengo\b", re.IGNORECASE),
        re.compile(r"\bqu[eé] recordatorios tengo\b", re.IGNORECASE),
    ],
    "proyecto": [
        re.compile(r"\bqu[eé] proyectos tengo\b", re.IGNORECASE),
        re.compile(r"\ben qu[eé] proyectos estoy\b", re.IGNORECASE),
        re.compile(r"\bmis proyectos\b", re.IGNORECASE),
    ],
    "preferencia": [
        re.compile(r"\bqu[eé] preferencias tengo\b", re.IGNORECASE),
        re.compile(r"\bmis preferencias\b", re.IGNORECASE),
    ],
    "ocupacion": [
        re.compile(r"\ben qu[eé] trabajo\b", re.IGNORECASE),
        re.compile(r"\bcu[aá]l es mi ocupaci[oó]n\b", re.IGNORECASE),
        re.compile(r"\ben qu[eé] trabajo estoy\b", re.IGNORECASE),
    ],
}

_LABELS = {
    "objetivos_pendientes": "pendientes",
    "proyecto": "proyectos",
    "preferencia": "preferencias",
    "ocupacion": "ocupación",
}


@dataclass
class GlobalContextQuery:
    section: str  # "objetivos_pendientes" | "proyecto" | "preferencia" | "ocupacion"


def detect_global_context_query(text: str) -> Optional[GlobalContextQuery]:
    """
    Devuelve a qué sección del digest se refiere la pregunta, si matchea
    alguno de los patrones conocidos. None si no matchea ninguno -- nunca
    se adivina; una frase ambigua o no prevista ("¿qué estoy haciendo?")
    simplemente no dispara nada acá.
    """
    text = (text or "").strip()
    if not text:
        return None

    for section, patterns in _SECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                return GlobalContextQuery(section=section)

    return None


def format_section_answer(digest: dict, query: GlobalContextQuery) -> str:
    """
    Arma una respuesta en lenguaje natural a partir de la sección del
    digest correspondiente. Determinístico, sin modelo.
    """
    label = _LABELS[query.section]

    if query.section == "objetivos_pendientes":
        items = digest.get("objetivos_pendientes", [])
    else:
        items = digest.get("hechos_por_categoria", {}).get(query.section, [])

    if not items:
        return f"No tenés {label} guardados todavía."

    if query.section == "objetivos_pendientes":
        listado = ", ".join(items)
        return f"Tenés {len(items)} pendiente{'s' if len(items) != 1 else ''}: {listado}."

    # Para hechos, mostrar el valor sin repetir el prefijo de categoría (ya lo sabe el label).
    valores = [item.split(":", 1)[1].strip() if ":" in item else item for item in items]
    listado = ", ".join(valores)
    return f"Tus {label}: {listado}."
