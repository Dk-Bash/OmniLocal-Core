"""
Capa de ranking híbrido (Bloque 5 — Semantic Retrieval Integration).

Combina resultados léxicos (RetrievalEngine.search_memory_lexical) y
semánticos (RetrievalEngine.search_semantic) como tres entradas
independientes -- keyword_score, semantic_score, importance -- en vez de
reemplazar la búsqueda léxica existente:

    final_score = keyword_score * w_keyword
                + semantic_score * w_semantic
                + importance     * w_importance

Solo se invoca desde local_ai/assistant.py cuando ya se decidió llamar al
modelo (después de descartar coincidencia directa y detección de hechos
por reglas): nunca se ejecuta antes, para no gastar embeddings de forma
innecesaria en preguntas que ya se responden desde memoria directa.

No reimplementa nada de RetrievalEngine: solo llama a sus métodos ya
existentes (search_memory_lexical, search_semantic) y combina resultados.
"""
from typing import List, Tuple

from local_ai.ollama_client import OllamaUnavailableError

# (peso keyword, peso semantic, peso importance)
DEFAULT_WEIGHTS: Tuple[float, float, float] = (0.5, 0.4, 0.1)


def hybrid_context(
    engine,
    query: str,
    ollama,
    base_context_chunks: List[str],
    weights: Tuple[float, float, float] = DEFAULT_WEIGHTS,
    min_semantic_similarity: float = 0.5,
    max_results: int = 5,
) -> List[str]:
    """
    Enriquece `base_context_chunks` (lo que ya arma context_builder.build_context:
    historial de sesión + memoria léxica) con memorias encontradas por
    similitud semántica que la búsqueda léxica no encontró, rankeadas por
    el score híbrido. Nunca reemplaza ni reordena lo que ya estaba en
    `base_context_chunks` -- solo agrega, sin duplicar.

    Si no hay modelo de embeddings disponible, si search_semantic() falla,
    o si no encuentra nada, devuelve `base_context_chunks` sin cambios --
    el mismo comportamiento que existía antes de este bloque.
    """
    if not ollama.has_embedding_model():
        return base_context_chunks

    retrieval_engine = engine.retrieval_engine

    try:
        semantic_results = retrieval_engine.search_semantic(query, ollama, min_similarity=min_semantic_similarity)
    except OllamaUnavailableError:
        return base_context_chunks
    except Exception:
        return base_context_chunks

    if not semantic_results:
        return base_context_chunks

    lexical_results = retrieval_engine.search_memory_lexical(query)
    keyword_score_by_id = {r.id: r.score for r in lexical_results}

    w_keyword, w_semantic, w_importance = weights
    scored = []
    for r in semantic_results:
        memory = retrieval_engine.memory_manager.get_memory(r.id)
        importance = memory.importance if memory else 0.0
        keyword_score = keyword_score_by_id.get(r.id, 0.0)
        final_score = keyword_score * w_keyword + r.score * w_semantic + importance * w_importance
        scored.append((final_score, r.content))

    scored.sort(key=lambda item: item[0], reverse=True)

    existing = set(base_context_chunks)
    extra_chunks: List[str] = []
    for _score, content in scored:
        if content in existing or content in extra_chunks:
            continue
        extra_chunks.append(content)
        if len(extra_chunks) >= max_results:
            break

    return base_context_chunks + extra_chunks
