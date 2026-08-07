"""
Observabilidad del conocimiento (Bloque 12 — Knowledge Observability
Layer). Solo mide y muestra -- no modifica memorias ni objetivos, no usa
el modelo. Depende de que los sistemas anteriores ya estén registrando
datos reales: `memory_history` (Bloque 6), `conversation_memory_usage`
(Bloque 6), `confidence` (Bloque 6/7), `goals.updated_at` (Bloque 12).

Deliberadamente NO combina las señales en un único "score de salud" --
cada candidato a revisión lista sus motivos por separado, explícitos, para
no crear una caja negra donde nadie sepa por qué un número salió como
salió.
"""
from datetime import datetime
from typing import List, Optional

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_UNUSED_DAYS_THRESHOLD = 180
DEFAULT_STALE_GOAL_DAYS_THRESHOLD = 120


def _parse_timestamp(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except ValueError:
        return None


def _days_since(timestamp: Optional[datetime], now: datetime) -> Optional[int]:
    if timestamp is None:
        return None
    return (now - timestamp).days


# ----------------------------------------------------------------
# Parte 1 -- Memory Insights
# ----------------------------------------------------------------
def build_memory_insights(
    engine,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    unused_days_threshold: int = DEFAULT_UNUSED_DAYS_THRESHOLD,
    now: Optional[datetime] = None,
) -> dict:
    """
    Estado actual de la memoria, sin modificar nada. Todas las señales se
    muestran por separado -- ver docstring del módulo.
    """
    now = now or datetime.now()
    memories = engine.get_all_memories()
    usage_summary = engine.db_manager.get_memory_usage_summary()
    change_counts = engine.db_manager.get_memory_change_counts()

    total_por_tipo: dict = {}
    confianza_baja: List[dict] = []
    nunca_usadas: List[dict] = []
    sin_uso_reciente: List[dict] = []
    mas_modificadas: List[dict] = []

    for memory in memories:
        total_por_tipo[memory.memory_type] = total_por_tipo.get(memory.memory_type, 0) + 1

        if memory.memory_type != "hecho":
            continue  # las señales de confianza/uso solo tienen sentido para hechos

        if memory.confidence < low_confidence_threshold:
            confianza_baja.append({"content": memory.content, "confidence": memory.confidence})

        usage = usage_summary.get(memory.id)
        if usage is None:
            nunca_usadas.append({"content": memory.content})
        else:
            last_used = _parse_timestamp(usage["last_used_at"])
            days = _days_since(last_used, now)
            if days is not None and days > unused_days_threshold:
                sin_uso_reciente.append({"content": memory.content, "dias_sin_uso": days})

        change_count = change_counts.get(memory.id, 0)
        if change_count > 0:
            mas_modificadas.append({"content": memory.content, "change_count": change_count})

    mas_modificadas.sort(key=lambda item: item["change_count"], reverse=True)

    return {
        "total_por_tipo": total_por_tipo,
        "confianza_baja": confianza_baja,
        "nunca_usadas": nunca_usadas,
        "sin_uso_reciente": sin_uso_reciente,
        "mas_modificadas": mas_modificadas,
    }


# ----------------------------------------------------------------
# Parte 2 -- Goal Insights
# ----------------------------------------------------------------
def build_goal_insights(
    engine,
    goal_manager,
    stale_days_threshold: int = DEFAULT_STALE_GOAL_DAYS_THRESHOLD,
    now: Optional[datetime] = None,
) -> dict:
    """Estado actual de los objetivos pendientes, sin marcar nada como abandonado."""
    now = now or datetime.now()
    pending = goal_manager.list_pending()

    vencidos: List[dict] = []
    sin_modificaciones_recientes: List[dict] = []

    for goal in pending:
        if goal.due_at is not None and goal.due_at < now:
            vencidos.append({"content": goal.content, "due_at": goal.due_at.isoformat()})

        reference = goal.updated_at or goal.created_at
        days = _days_since(reference, now)
        if days is not None and days > stale_days_threshold:
            sin_modificaciones_recientes.append({"content": goal.content, "dias_sin_cambios": days})

    return {
        "pendientes_actuales": len(pending),
        "vencidos": vencidos,
        "sin_modificaciones_recientes": sin_modificaciones_recientes,
    }


# ----------------------------------------------------------------
# Parte 3 -- Review Candidates (motivos separados, nunca un score combinado)
# ----------------------------------------------------------------
def build_review_candidates(
    engine,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    unused_days_threshold: int = DEFAULT_UNUSED_DAYS_THRESHOLD,
    now: Optional[datetime] = None,
) -> list:
    """
    Lista de memorias que podrían merecer revisión, con sus motivos
    explícitos por separado -- nunca un score único combinado. Una misma
    memoria puede tener más de un motivo, listados aparte.

    Bloque 13 (Assisted Knowledge Review): expone `id` (necesario para
    poder actuar sobre un candidato) y excluye memorias con
    `review_status == "ignorado"`. "Confirmado" y "corregido" no
    necesitan filtro propio: al confirmar sube `confidence`, al corregir
    queda en 1.0 -- en ambos casos dejan de cumplir el umbral de
    "confianza baja" por sí solos, sin lógica extra acá.
    """
    now = now or datetime.now()
    memories = engine.get_all_memories()
    usage_summary = engine.db_manager.get_memory_usage_summary()

    reasons_by_id: dict = {}
    content_by_id: dict = {}

    for memory in memories:
        if memory.memory_type != "hecho":
            continue
        if memory.review_status == "ignorado":
            continue

        content_by_id[memory.id] = memory.content

        if memory.confidence < low_confidence_threshold:
            reasons_by_id.setdefault(memory.id, []).append(f"confianza baja ({memory.confidence:.2f})")

        usage = usage_summary.get(memory.id)
        if usage is not None:
            last_used = _parse_timestamp(usage["last_used_at"])
            days = _days_since(last_used, now)
            if days is not None and days > unused_days_threshold:
                reasons_by_id.setdefault(memory.id, []).append(f"sin uso hace {days} días")

    return [
        {"id": memory_id, "content": content_by_id[memory_id], "reasons": reasons}
        for memory_id, reasons in reasons_by_id.items()
    ]
