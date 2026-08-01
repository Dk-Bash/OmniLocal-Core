"""
Constructor de contexto conversacional (Bloque 2 — OmniLocal Intelligence Upgrade).

Combina dos fuentes de contexto para el modelo local, sin duplicar ninguna:
1. Memoria corta: los últimos turnos de la sesión activa (para resolver
   referencias como "agregale memoria a ESO" cuando "eso" fue mencionado en
   el mensaje anterior de la misma charla).
2. Memoria larga: los resultados de `RetrievalEngine`/`engine.search()` que
   ya existían antes de este bloque (memoria guardada + conocimiento,
   ranqueados por palabras clave).

No crea ningún sistema de memoria nuevo: lee `conversations` a través de
`SQLiteManager.get_conversations()` (ya existente) y `engine.search()` (ya
existente). Sesiones distintas nunca se mezclan: si no hay `session_id`, no
se agrega memoria corta en absoluto.

Nota sobre el orden de `get_conversations`: con `session_id` la consulta ya
devuelve los turnos en orden cronológico ascendente. Para "los últimos N"
turnos, se traen todos los de la sesión y se recorta en Python (sin tocar
`SQLiteManager`) — el volumen por sesión de una app local de un usuario es
chico, así que no hay costo de performance real.
"""
from typing import List, Optional

DEFAULT_MAX_TURNS = 6
DEFAULT_MAX_CHARS = 2000
DEFAULT_MAX_RETRIEVAL_RESULTS = 5


def _recent_session_turns(engine, session_id: int, max_turns: int) -> List[str]:
    """Últimos `max_turns` turnos de la sesión, formateados y en orden cronológico."""
    rows = engine.db_manager.get_conversations(session_id=session_id)
    recent = rows[-max_turns:] if max_turns > 0 else []
    return [f"Usuario: {row['user_input']}\nAsistente: {row['assistant_response']}" for row in recent]


def _truncate_to_budget(session_chunks: List[str], retrieval_chunks: List[str], max_chars: int) -> List[str]:
    """
    Combina ambas listas y recorta para no superar `max_chars` en total.
    Se descarta primero lo más viejo de la conversación (session_chunks[0],
    [1], ...); si aún sobra, se descarta lo menos relevante del retrieval
    (el final de la lista, que ya viene ordenada por score descendente).
    """
    session_chunks = list(session_chunks)
    retrieval_chunks = list(retrieval_chunks)

    def total_len(a: List[str], b: List[str]) -> int:
        return sum(len(c) for c in a) + sum(len(c) for c in b)

    while total_len(session_chunks, retrieval_chunks) > max_chars and (session_chunks or retrieval_chunks):
        if session_chunks:
            session_chunks.pop(0)  # el turno más viejo primero
        elif retrieval_chunks:
            retrieval_chunks.pop()  # el resultado menos relevante primero

    return session_chunks + retrieval_chunks


def build_context(
    engine,
    query: str,
    session_id: Optional[int] = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_retrieval_results: int = DEFAULT_MAX_RETRIEVAL_RESULTS,
) -> List[str]:
    """
    Arma la lista de fragmentos de contexto para pasarle al modelo local:
    memoria corta de la sesión activa (si hay `session_id`) + memoria larga
    ya recuperada por `engine.search()`, truncado a `max_chars` en total.
    """
    session_chunks = _recent_session_turns(engine, session_id, max_turns) if session_id is not None else []

    results = engine.search(query)
    retrieval_chunks = [r.content for r in results[:max_retrieval_results]]

    return _truncate_to_budget(session_chunks, retrieval_chunks, max_chars)
