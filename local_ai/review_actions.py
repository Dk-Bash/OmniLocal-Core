"""
Acciones de revisión asistida (Bloque 13 — Assisted Knowledge Review
Layer). El usuario decide, el sistema registra -- ninguna de estas
funciones actúa sola; todas requieren que algo externo (CLI, API) las
dispare con una decisión explícita del usuario sobre un candidato de
`local_ai/knowledge_observability.py::build_review_candidates()`.

Tres acciones, con efectos distintos a propósito (una confirmación y una
corrección son señales de fuerza distinta):
- confirmar: la memoria sigue siendo válida tal cual está -> sube
  `confidence` un poco (mismo delta que el feedback del Bloque 7, no un
  número nuevo). No toca el contenido.
- corregir: el usuario da el valor correcto -> reemplaza el contenido,
  deja rastro en `memory_history` (Bloque 6), y resetea `confidence` al
  máximo -- es la señal más fuerte posible, el usuario entregó el dato
  directamente.
- ignorar: no cambia nada del contenido ni de la confianza, solo marca
  que ya se revisó y se decidió no actuar. Nota conocida, documentada a
  propósito: un "ignorado" no expira todavía -- queda oculto de
  build_review_candidates() para siempre hasta que algo más lo cambie
  (por ejemplo, una corrección posterior). No se resuelve en este
  bloque.
"""
from local_ai.feedback_learning import DEFAULT_DELTA

CORRECTION_CONFIDENCE = 1.0


def confirm_memory(engine, memory_id: int, delta: float = DEFAULT_DELTA) -> bool:
    """El usuario confirma que la memoria sigue siendo válida tal cual está."""
    memory = engine.memory_manager.get_memory(memory_id)
    if memory is None:
        return False
    new_confidence = min(1.0, memory.confidence + delta)
    engine.db_manager.update_memory(memory_id, memory.content, confidence=new_confidence)
    engine.db_manager.mark_memory_reviewed(memory_id, "confirmado")
    return True


def correct_memory(engine, memory_id: int, new_content: str) -> bool:
    """El usuario corrige el contenido de la memoria -- la señal más fuerte disponible."""
    memory = engine.memory_manager.get_memory(memory_id)
    if memory is None:
        return False
    engine.db_manager.insert_memory_history(memory_id, memory.content, new_content)
    engine.db_manager.update_memory(memory_id, new_content, confidence=CORRECTION_CONFIDENCE)
    engine.db_manager.mark_memory_reviewed(memory_id, "corregido")
    return True


def ignore_memory(engine, memory_id: int) -> bool:
    """El usuario decide no actuar sobre este candidato -- no cambia contenido ni confianza."""
    memory = engine.memory_manager.get_memory(memory_id)
    if memory is None:
        return False
    engine.db_manager.mark_memory_reviewed(memory_id, "ignorado")
    return True
