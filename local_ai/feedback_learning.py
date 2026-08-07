"""
Aprendizaje por feedback (Bloque 7 — Feedback Confidence Learning).

Cuando el usuario marca una respuesta como útil o no útil, ajusta la
`confidence` (Bloque 6) de las memorias que participaron en esa respuesta,
según `conversation_memory_usage` (trazabilidad aproximada, también
Bloque 6). Deliberadamente NO toca `importance` (Bloque 3): son conceptos
distintos -- importancia es cuánto pesa en el ranking; confianza es qué
tan vigente/confiable sigue pareciendo el dato, y es justo lo que el
feedback del usuario debería poder mover con el tiempo.

No modifica local_ai/assistant.py::ask() en absoluto. Se dispara solo
desde LocalAssistant.feedback(), un método aparte, de bajo tráfico, fuera
del camino crítico de la conversación (el que ya rompimos dos veces y no
queremos volver a tocar sin necesidad).
"""
from typing import List

from app.logger import get_logger

logger = get_logger(__name__)

# Ajuste pequeño y deliberado: el feedback mueve la confianza de a poco,
# no de un salto -- hacen falta varias señales en el mismo sentido para
# que una memoria suba o baje mucho.
DEFAULT_DELTA = 0.05


def apply_feedback_to_memories(engine, conversation_id: int, useful: bool, delta: float = DEFAULT_DELTA) -> List[int]:
    """
    Ajusta la confidence de las memorias vinculadas a `conversation_id` vía
    conversation_memory_usage. Devuelve los `memory_id` efectivamente
    ajustados (puede ser una lista vacía si no hay memorias asociadas, o si
    ya estaban en el límite 0.0/1.0). Nunca lanza excepción -- si algo
    falla, deja un warning y devuelve lista vacía, para no romper el
    registro del feedback en sí.
    """
    try:
        usage_rows = engine.db_manager.get_conversation_memory_usage(conversation_id)
    except Exception as exc:
        logger.warning(f"No se pudo leer conversation_memory_usage para la conversación {conversation_id}: {exc}")
        return []

    if not usage_rows:
        return []

    sign = 1 if useful else -1
    adjusted: List[int] = []

    for row in usage_rows:
        memory_id = row["memory_id"]
        memory = engine.memory_manager.get_memory(memory_id)
        if memory is None:
            continue  # la memoria pudo haberse borrado desde entonces

        new_confidence = max(0.0, min(1.0, memory.confidence + sign * delta))
        if new_confidence == memory.confidence:
            continue  # ya estaba en el límite, no hay nada que mover

        engine.db_manager.update_memory(memory_id, memory.content, confidence=new_confidence)
        adjusted.append(memory_id)

    return adjusted
