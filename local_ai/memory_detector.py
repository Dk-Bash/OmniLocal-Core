"""
Detector de memoria automática (Bloque 1 — OmniLocal Intelligence Upgrade).

Decide, después de cada interacción, si lo que escribió el usuario contiene
un dato reutilizable (nombre, ocupación, proyecto, preferencia, etc.) que
conviene guardar como memoria de tipo "hecho" en vez de como charla
genérica. Reemplaza el guardado ciego que existía antes en
`LocalAssistant.ask()`.

Dos caminos, para funcionar con o sin el modelo de IA local:
1. Con Ollama disponible: se le pide al modelo clasificar en un formato muy
   corto y acotado (una línea, "CATEGORIA: dato" o "NADA").
2. Sin Ollama (modo "solo memoria"), o si el modelo no devuelve nada
   aprovechable: un conjunto chico de patrones conocidos en español sirve de
   red de seguridad, sin ninguna dependencia de red.

No crea ningún sistema nuevo: reutiliza el mismo `OllamaClient.generate()`
que ya existe. La categoría se guarda en `memory_type` (columna de texto
libre que ya existe en la tabla `memories`), sin migrar el esquema.

Se usa deliberadamente el nombre `MemoryCandidate` (no `FactCandidate`) para
dejar abierta la evolución futura a otras categorías de memoria automática
(preferencias, proyectos, contactos, etc.) sin tener que renombrar nada.
"""
import re
from dataclasses import dataclass
from typing import Optional

from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from app.logger import get_logger

logger = get_logger(__name__)

CATEGORIES = {"nombre", "ocupacion", "proyecto", "preferencia", "otro"}

# Entradas más largas que esto se tratan como charla elaborada, no como un
# dato aislado, para no terminar guardando párrafos enteros como "hecho".
MAX_INPUT_LENGTH_FOR_RULES = 300

_QUESTION_STARTS = (
    "que ", "qué ", "como ", "cómo ", "cual ", "cuál ", "cuando ", "cuándo ",
    "donde ", "dónde ", "quien ", "quién ", "por que", "por qué",
)

_RULE_PATTERNS = [
    (re.compile(r"\bmi nombre es ([^.,;\n]{2,60})", re.IGNORECASE), "nombre"),
    (re.compile(r"\bme llamo ([^.,;\n]{2,60})", re.IGNORECASE), "nombre"),
    (re.compile(r"\btrabajo (?:como|de) ([^.,;\n]{2,60})", re.IGNORECASE), "ocupacion"),
    (re.compile(r"\bestoy estudiando ([^.,;\n]{2,60})", re.IGNORECASE), "ocupacion"),
    (re.compile(r"\bmi proyecto se llama ([^.,;\n]{2,60})", re.IGNORECASE), "proyecto"),
    (re.compile(r"\bprefiero ([^.,;\n]{2,60})", re.IGNORECASE), "preferencia"),
]

_MODEL_SYSTEM_PROMPT = (
    "Sos un clasificador. Te paso un mensaje de un usuario. Si el mensaje "
    "contiene un dato personal reutilizable (nombre, ocupación, proyecto, "
    "preferencia u otro dato de contexto), respondé en una sola línea con "
    "el formato exacto 'CATEGORIA: dato normalizado en pocas palabras'. "
    "Las categorías válidas son: nombre, ocupacion, proyecto, preferencia, "
    "otro. Si el mensaje NO contiene ningún dato reutilizable (es una "
    "pregunta, un saludo, o un comentario sin datos concretos), respondé "
    "exactamente: NADA. No agregues explicaciones ni texto adicional."
)


@dataclass
class MemoryCandidate:
    """Dato candidato a guardarse como memoria automática."""
    content: str
    memory_type: str = "hecho"
    importance: float = 0.75


def _looks_like_question(text: str) -> bool:
    stripped = text.strip()
    if stripped.endswith("?") or stripped.startswith("¿"):
        return True
    lowered = stripped.lower()
    return any(lowered.startswith(w) for w in _QUESTION_STARTS)


def detect_by_rules(user_input: str) -> Optional[MemoryCandidate]:
    """
    Camino de respaldo sin modelo: patrones conocidos en español. Se usa
    cuando Ollama no está disponible, o como red de seguridad si el modelo
    no devolvió nada aprovechable.
    """
    user_input = (user_input or "").strip()
    if not user_input or len(user_input) > MAX_INPUT_LENGTH_FOR_RULES:
        return None
    if _looks_like_question(user_input):
        return None

    for pattern, category in _RULE_PATTERNS:
        match = pattern.search(user_input)
        if not match:
            continue
        detail = match.group(1).strip().rstrip(".!¡¿? ")
        if not detail:
            continue
        label = "Nombre" if category == "nombre" else category.capitalize()
        return MemoryCandidate(content=f"{label}: {detail}", memory_type="hecho", importance=0.75)
    return None


def detect_by_model(user_input: str, ollama: OllamaClient) -> Optional[MemoryCandidate]:
    """
    Camino principal: le pide al modelo local clasificar el mensaje en un
    formato corto y acotado. Devuelve None si el modelo no está disponible,
    no responde en el formato esperado, o indica explícitamente "NADA".
    """
    try:
        raw = ollama.generate(prompt=user_input, system=_MODEL_SYSTEM_PROMPT)
    except OllamaUnavailableError as exc:
        logger.warning(f"Detector de memoria: no se pudo consultar el modelo, se usa el camino de reglas. {exc}")
        return None

    raw = (raw or "").strip()
    if not raw or raw.upper().startswith("NADA"):
        return None
    if ":" not in raw:
        return None

    category, _, detail = raw.partition(":")
    category = category.strip().lower()
    detail = detail.strip()
    if not detail or category not in CATEGORIES:
        return None

    return MemoryCandidate(content=f"{category.capitalize()}: {detail}", memory_type="hecho", importance=0.75)


def detect_memory_candidate(user_input: str, ollama: Optional[OllamaClient] = None) -> Optional[MemoryCandidate]:
    """
    Punto de entrada del detector. Intenta primero con el modelo local (si
    está disponible); si no hay modelo, o no encuentra nada aprovechable,
    cae al camino de reglas. Nunca lanza excepción: en el peor caso
    devuelve None y el llamador debe conservar su comportamiento anterior.
    """
    user_input = (user_input or "").strip()
    if not user_input:
        return None

    if ollama is not None:
        try:
            if ollama.is_available():
                candidate = detect_by_model(user_input, ollama)
                if candidate is not None:
                    return candidate
        except Exception as exc:  # el detector nunca debe romper el flujo principal de ask()
            logger.warning(f"Detector de memoria: error inesperado consultando el modelo: {exc}")

    return detect_by_rules(user_input)
