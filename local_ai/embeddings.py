"""
Embeddings semánticos locales (Bloque 4A — Semantic Retrieval, parte A).

Genera y guarda vectores de embedding para memorias, usando el modelo de
embeddings de Ollama (separado del modelo de lenguaje, ver
local_ai/ollama_client.py::embed()). Es infraestructura aislada: todavía no
se usa para responder preguntas -- eso es el Bloque 4B, a definir aparte.
`retrieval/engine.py::search_semantic()` es quien la consulta, también
separado de `search()`.

La generación del embedding va en un hilo de fondo (no bloqueante): guardar
la memoria y responder al usuario es rápido, pero pedirle un embedding a
Ollama puede tardar -- no debe agregar esa espera a la respuesta que ve el
usuario. Mismo criterio que ya se usó para el detector del Bloque 1.
"""
import math
import threading
from typing import List, Optional

from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from app.logger import get_logger

logger = get_logger(__name__)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Similitud coseno entre dos vectores. Devuelve 0.0 para vectores vacíos,
    de largo distinto, o con norma cero (en vez de lanzar una excepción).
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def generate_and_store_embedding(engine, memory_id: int, content: str, ollama: OllamaClient) -> bool:
    """
    Genera el embedding de `content` y lo guarda asociado a `memory_id`.
    Nunca lanza excepción -- si algo falla (sin modelo, sin Ollama, error de
    red), devuelve False y la memoria queda igual de guardada, solo que sin
    vector todavía (se puede regenerar más adelante).
    """
    try:
        if not ollama.has_embedding_model():
            return False
        vector = ollama.embed(content)
        if not vector:
            return False
        engine.db_manager.upsert_memory_embedding(memory_id=memory_id, vector=vector, model=ollama.embed_model)
        return True
    except OllamaUnavailableError as exc:
        logger.warning(f"No se pudo generar el embedding de la memoria {memory_id}: {exc}")
        return False
    except Exception as exc:  # nunca debe romper el flujo principal de la conversación
        logger.warning(f"Error inesperado generando embedding de la memoria {memory_id}: {exc}")
        return False


def generate_and_store_embedding_async(
    engine, memory_id: int, content: str, ollama: OllamaClient
) -> threading.Thread:
    """
    Igual que generate_and_store_embedding, pero en un hilo de fondo (no
    bloqueante). Devuelve el hilo iniciado -- los llamadores normales lo
    ignoran (fire-and-forget); los tests pueden hacer .join() para esperarlo
    de forma determinística.
    """
    thread = threading.Thread(
        target=generate_and_store_embedding,
        args=(engine, memory_id, content, ollama),
        daemon=True,
    )
    thread.start()
    return thread
