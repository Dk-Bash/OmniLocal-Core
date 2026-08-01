import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from local_ai.embeddings import (
    cosine_similarity,
    generate_and_store_embedding,
    generate_and_store_embedding_async,
)


@pytest.fixture
def engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    eng = OmniLocalEngine(db_manager=db_manager)
    eng.start()
    yield eng
    db_manager.close()
    os.remove(path)


# ----------------------------------------------------------------
# cosine_similarity (matemática pura, sin dependencias)
# ----------------------------------------------------------------
def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_handles_empty_or_mismatched_vectors():
    assert cosine_similarity([], [1.0, 2.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0  # norma cero


# ----------------------------------------------------------------
# Generación y guardado de embeddings (con Ollama mockeado)
# ----------------------------------------------------------------
def test_generate_and_store_embedding_success(engine):
    mem_id = engine.save_memory(content="El proyecto se llama OmniLocal", memory_type="hecho", importance=0.75)
    client = OllamaClient()

    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.1, 0.2, 0.3]):
        ok = generate_and_store_embedding(engine, mem_id, "El proyecto se llama OmniLocal", client)

    assert ok is True
    stored = engine.db_manager.get_memory_embedding(mem_id)
    assert stored is not None
    assert stored["vector"] == [0.1, 0.2, 0.3]
    assert stored["model"] == client.embed_model


def test_generate_and_store_embedding_returns_false_without_embedding_model(engine):
    mem_id = engine.save_memory(content="algo", memory_type="hecho")
    client = OllamaClient()

    with patch.object(OllamaClient, "has_embedding_model", return_value=False):
        ok = generate_and_store_embedding(engine, mem_id, "algo", client)

    assert ok is False
    assert engine.db_manager.get_memory_embedding(mem_id) is None


def test_generate_and_store_embedding_never_raises_on_ollama_error(engine):
    mem_id = engine.save_memory(content="algo", memory_type="hecho")
    client = OllamaClient()

    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", side_effect=OllamaUnavailableError("boom")):
        ok = generate_and_store_embedding(engine, mem_id, "algo", client)

    assert ok is False  # no lanza excepcion, solo devuelve False


def test_generate_and_store_embedding_async_does_not_block_and_completes(engine):
    mem_id = engine.save_memory(content="El proyecto se llama OmniLocal", memory_type="hecho")
    client = OllamaClient()

    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.5, 0.5]):
        thread = generate_and_store_embedding_async(engine, mem_id, "El proyecto se llama OmniLocal", client)
        thread.join(timeout=5)  # test determinista: esperamos el hilo, en producción nadie lo hace

    assert engine.db_manager.get_memory_embedding(mem_id) is not None


# ----------------------------------------------------------------
# search_semantic() -- separado de search(), con embeddings simulados
# ----------------------------------------------------------------
def test_search_semantic_ranks_by_similarity(engine):
    id_a = engine.save_memory(content="Mi proyecto se llama OmniLocal", memory_type="hecho")
    id_b = engine.save_memory(content="Hoy llovió mucho en Buenos Aires", memory_type="conversacion")

    # Vectores simulados: el de "proyecto" es casi igual al de la consulta,
    # el del clima es prácticamente ortogonal.
    engine.db_manager.upsert_memory_embedding(id_a, [1.0, 0.0, 0.0], "modelo-test")
    engine.db_manager.upsert_memory_embedding(id_b, [0.0, 1.0, 0.0], "modelo-test")

    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.9, 0.1, 0.0]):
        results = engine.retrieval_engine.search_semantic("como se llama mi proyecto", ollama=client)

    assert len(results) == 1  # el otro cae por debajo de min_similarity
    assert results[0].source_type == "memory_semantic"
    assert "OmniLocal" in results[0].content


def test_search_semantic_returns_empty_without_embedding_model(engine):
    engine.save_memory(content="algo", memory_type="hecho")
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=False):
        results = engine.retrieval_engine.search_semantic("algo", ollama=client)
    assert results == []


def test_search_semantic_returns_empty_on_ollama_error(engine):
    engine.save_memory(content="algo", memory_type="hecho")
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", side_effect=OllamaUnavailableError("boom")):
        results = engine.retrieval_engine.search_semantic("algo", ollama=client)
    assert results == []


def test_search_semantic_does_not_affect_default_search(engine):
    """Confirma explícitamente la condición de la aprobación: search() no cambió."""
    mem_id = engine.save_memory(content="Mi proyecto se llama OmniLocal", memory_type="hecho")
    engine.db_manager.upsert_memory_embedding(mem_id, [1.0, 0.0], "modelo-test")

    # Sin ninguna palabra clave compartida -> search() (léxico) sigue sin encontrar nada,
    # exactamente el comportamiento que protege test_no_overlap_returns_no_results.
    results = engine.search("como me llamo yo")
    assert results == []
