"""
Consolidación adaptativa de memoria (Bloque 6 — Adaptive Memory Consolidation Layer).

Los hechos que detecta local_ai/memory_detector.py siempre tienen la forma
"Categoria: valor" (categorías fijas: nombre, ocupacion, proyecto,
preferencia, otro). Esa estructura es la base de este módulo: no hace
falta NLP para saber "de qué se está hablando" en una declaración nueva --
ya viene etiquetado.

Dos comportamientos, según la categoría:
- nombre / ocupacion: valor único vigente. Una declaración nueva de la
  misma categoría ACTUALIZA el hecho existente (con historial de qué
  decía antes), en vez de crear una fila nueva.
- proyecto / preferencia / otro: colección. Una persona puede tener varios
  proyectos o preferencias simultáneas y todas válidas -- acá se
  deduplica (no se inserta si ya existe algo casi idéntico) pero nunca se
  sobreescribe un valor distinto por otro.

No toca omnilocal_runtime, no implementa aprendizaje por feedback, no
borra memorias automáticamente -- todo eso queda fuera de este bloque.
"""
from typing import List, Optional

from local_ai.memory_detector import MemoryCandidate
from app.logger import get_logger

logger = get_logger(__name__)

# Categorías tratadas como "valor único vigente" (se actualizan).
SINGLE_VALUE_CATEGORIES = {"nombre", "ocupacion"}

# Categorías tratadas como "colección" (se deduplican, nunca se sobreescriben).
COLLECTION_CATEGORIES = {"proyecto", "preferencia", "otro"}

# Umbral de similitud semántica para considerar dos elementos de una
# colección como "el mismo dato repetido". Deliberadamente alto: mejor
# quedarse corto deduplicando que fusionar por error dos proyectos
# distintos.
NEAR_DUPLICATE_MIN_SIMILARITY = 0.9


def _extract_category(content: str) -> Optional[str]:
    """Extrae la categoría de un contenido tipo 'Categoria: valor'. None si no matchea el formato."""
    if ":" not in content:
        return None
    label = content.split(":", 1)[0].strip().lower()
    if label in SINGLE_VALUE_CATEGORIES or label in COLLECTION_CATEGORIES:
        return label
    return None


def _existing_hechos_by_category(engine, category: str) -> List:
    """Recorrido simple sobre las memorias tipo 'hecho' con el prefijo de esa categoría exacta."""
    prefix = f"{category.capitalize()}:"
    return [
        m for m in engine.get_all_memories()
        if m.memory_type == "hecho" and m.content.lower().startswith(prefix.lower())
    ]


def _find_near_duplicate(engine, category: str, content: str, ollama=None) -> Optional[object]:
    """
    Busca, entre los hechos existentes de la misma categoría, uno casi
    idéntico al contenido nuevo. Primero coincidencia exacta (barata,
    determinística); si no hay, y hay embeddings disponibles, similitud
    semántica con umbral alto.
    """
    existing = _existing_hechos_by_category(engine, category)

    for mem in existing:
        if mem.content.strip().lower() == content.strip().lower():
            return mem

    if ollama is not None:
        try:
            if ollama.has_embedding_model():
                semantic_results = engine.retrieval_engine.search_semantic(
                    content, ollama, min_similarity=NEAR_DUPLICATE_MIN_SIMILARITY
                )
                semantic_ids = {r.id for r in semantic_results}
                for mem in existing:
                    if mem.id in semantic_ids:
                        return mem
        except Exception as exc:  # la consolidación nunca debe romper el guardado
            logger.warning(f"No se pudo verificar duplicado semántico: {exc}")

    return None


def consolidate_fact(engine, candidate: MemoryCandidate, ollama=None) -> int:
    """
    Punto de entrada del Bloque 6. Decide si el hecho detectado actualiza
    algo existente, se deduplica, o se guarda como fila nueva -- según la
    categoría. Devuelve el `memory_id` resultante (nuevo o existente).
    """
    category = _extract_category(candidate.content)

    if category is None:
        # No matchea el formato "Categoria: valor" esperado -- guardar tal
        # cual, sin intentar consolidar (comportamiento anterior a este bloque).
        return engine.save_memory(
            content=candidate.content, memory_type=candidate.memory_type, importance=candidate.importance
        )

    if category in SINGLE_VALUE_CATEGORIES:
        existing_list = _existing_hechos_by_category(engine, category)
        existing = existing_list[0] if existing_list else None
        if existing is None:
            return engine.save_memory(
                content=candidate.content, memory_type=candidate.memory_type, importance=candidate.importance
            )
        if existing.content.strip() == candidate.content.strip():
            return existing.id  # nada cambió, no hace falta tocar nada
        engine.db_manager.insert_memory_history(existing.id, existing.content, candidate.content)
        engine.db_manager.update_memory(
            existing.id, candidate.content, importance=candidate.importance, confidence=1.0
        )
        return existing.id

    # Categorías de colección: deduplicar, nunca sobreescribir.
    duplicate = _find_near_duplicate(engine, category, candidate.content, ollama=ollama)
    if duplicate is not None:
        return duplicate.id

    return engine.save_memory(
        content=candidate.content, memory_type=candidate.memory_type, importance=candidate.importance
    )
