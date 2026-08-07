"""
Agregación directa de contexto personal (Bloque 11A — Personal Context
Aggregation).

Distinto de retrieval/: no busca por relevancia a una consulta, junta
TODO lo que corresponde a cada categoría, directamente desde
MemoryManager/GoalManager -- sin pasar por search() en absoluto, sin
tocar Ollama en ningún punto.

Esto es la base para bloques futuros:
- Bloque 11B (Personal Context Awareness): detectar preguntas globales
  ("¿qué tengo pendiente?") e integrarlas a local_ai/assistant.py::ask().
- Bloque 11C (Personal Summary Intelligence): usar el modelo para
  sintetizar/priorizar el digest, no solo listarlo.

Ninguno de los dos se implementa acá -- este módulo no se conecta a
ask() todavía, a propósito.
"""
from collections import defaultdict
from typing import Dict, List, Optional

from local_ai.memory_consolidation import extract_category

# Bloque 11C: límite por defecto al pasar el digest completo como contexto
# a un modelo -- más generoso que el de context_builder.py (2000) porque
# acá el objetivo es ser comprensivo a propósito, no un top-N por relevancia.
DEFAULT_MAX_DIGEST_CHARS = 3000
MAX_ITEMS_PER_SECTION = 15


def build_profile_digest(engine, goal_manager) -> dict:
    """
    Arma un resumen completo y determinístico del estado actual del
    usuario: hechos agrupados por categoría (nombre, ocupacion, proyecto,
    preferencia, otro) y objetivos pendientes. No usa ranking ni
    relevancia -- es una consulta completa, no una búsqueda.
    """
    hechos_por_categoria: Dict[str, List[str]] = defaultdict(list)
    sin_categoria: List[str] = []

    for memory in engine.get_all_memories():
        if memory.memory_type != "hecho":
            continue
        category = extract_category(memory.content)
        if category is None:
            sin_categoria.append(memory.content)
        else:
            hechos_por_categoria[category].append(memory.content)

    pending_goals = goal_manager.list_pending()

    return {
        "hechos_por_categoria": dict(hechos_por_categoria),
        "hechos_sin_categoria": sin_categoria,
        "objetivos_pendientes": [g.content for g in pending_goals],
    }


def format_profile_digest_as_text(digest: dict, max_chars: Optional[int] = None) -> str:
    """
    Convierte el digest a texto legible, listo para mostrarse o para
    pasarse como contexto a un modelo (Bloque 11C).

    `max_chars=None` (default): sin límite -- comportamiento original del
    Bloque 11A/11B, sin cambios. Si se pasa un límite, se acota primero la
    cantidad de ítems por sección (MAX_ITEMS_PER_SECTION) y después, si
    todavía excede `max_chars`, se recorta el texto final con un aviso
    explícito -- nunca se corta a mitad de una palabra sin avisar.
    """
    lines: List[str] = []

    hechos = digest.get("hechos_por_categoria", {})
    if hechos:
        lines.append("Hechos guardados:")
        for category in sorted(hechos.keys()):
            items = hechos[category]
            if max_chars is not None:
                items = items[:MAX_ITEMS_PER_SECTION]
            for item in items:
                lines.append(f"  - {item}")

    sin_categoria = digest.get("hechos_sin_categoria", [])
    if sin_categoria:
        lines.append("Otros datos guardados:")
        items = sin_categoria[:MAX_ITEMS_PER_SECTION] if max_chars is not None else sin_categoria
        for item in items:
            lines.append(f"  - {item}")

    pendientes = digest.get("objetivos_pendientes", [])
    if pendientes:
        lines.append("Objetivos pendientes:")
        items = pendientes[:MAX_ITEMS_PER_SECTION] if max_chars is not None else pendientes
        for item in items:
            lines.append(f"  - {item}")

    if not lines:
        return "Todavía no hay hechos ni objetivos guardados."

    text = "\n".join(lines)

    if max_chars is not None and len(text) > max_chars:
        cutoff = max_chars - len("\n... (se omitieron algunos datos por espacio)")
        cutoff = max(cutoff, 0)
        text = text[:cutoff].rstrip() + "\n... (se omitieron algunos datos por espacio)"

    return text
