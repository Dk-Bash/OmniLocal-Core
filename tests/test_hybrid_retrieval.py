import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from retrieval.hybrid import hybrid_context, DEFAULT_WEIGHTS


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
# Caso 1: encontrar memoria sin palabras compartidas, vía embeddings
# ----------------------------------------------------------------
def test_finds_memory_with_no_shared_keywords_via_embeddings(engine):
    mem_id = engine.save_memory(content="Mi proyecto se llama OmniLocal", memory_type="hecho", importance=0.75)
    engine.db_manager.upsert_memory_embedding(mem_id, [1.0, 0.0, 0.0], "modelo-test")

    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.95, 0.05, 0.0]):
        result = hybrid_context(engine, "como se llama mi proyecto", client, base_context_chunks=[])

    assert any("OmniLocal" in c for c in result)


# ----------------------------------------------------------------
# Caso 2: ranking correcto (keyword fuerte/semantica baja vs. keyword baja/semantica alta)
# ----------------------------------------------------------------
def test_hybrid_ranking_orders_by_combined_score(engine):
    # A: coincide PARCIALMENTE por palabras clave (comparte "horario" pero
    # no "taller"), y el vector esta lejos de la consulta.
    id_a = engine.save_memory(content="El horario del colectivo cambio", memory_type="hecho", importance=0.5)
    engine.db_manager.upsert_memory_embedding(id_a, [0.0, 1.0, 0.0], "modelo-test")

    # B: no comparte ninguna palabra clave, pero el vector es casi identico a la consulta.
    id_b = engine.save_memory(content="Arranca temprano y termina a la tarde el evento", memory_type="hecho", importance=0.5)
    engine.db_manager.upsert_memory_embedding(id_b, [1.0, 0.0, 0.0], "modelo-test")

    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.99, 0.01, 0.0]):
        result = hybrid_context(
            engine, "horario del taller", client, base_context_chunks=[],
            weights=(0.5, 0.4, 0.1), min_semantic_similarity=0.0,
        )

    # A: keyword_score=0.5 (comparte "horario", no "taller"), semantic bajo (~0.01), importance=0.5
    #    -> 0.5*0.5 + 0.01*0.4 + 0.5*0.1 ~= 0.304
    # B: keyword_score=0.0, semantic altisimo (~1.0), importance=0.5
    #    -> 0.0*0.5 + 1.0*0.4 + 0.5*0.1 ~= 0.45
    # B deberia ganar con estos pesos.
    idx_a = next(i for i, c in enumerate(result) if "colectivo" in c)
    idx_b = next(i for i, c in enumerate(result) if "Arranca" in c)
    assert idx_b < idx_a


# ----------------------------------------------------------------
# Caso 3: sin modelo de embeddings -> contexto identico al anterior
# ----------------------------------------------------------------
def test_without_embedding_model_returns_base_context_unchanged(engine):
    engine.save_memory(content="algo irrelevante", memory_type="hecho")
    client = OllamaClient()
    base = ["Usuario: hola\nAsistente: hola", "una memoria cualquiera"]

    with patch.object(OllamaClient, "has_embedding_model", return_value=False):
        result = hybrid_context(engine, "cualquier cosa", client, base_context_chunks=base)

    assert result == base


def test_semantic_search_failure_falls_back_to_base_context(engine):
    client = OllamaClient()
    base = ["contexto original"]
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", side_effect=OllamaUnavailableError("boom")):
        result = hybrid_context(engine, "algo", client, base_context_chunks=base)
    assert result == base


def test_no_semantic_results_returns_base_context_unchanged(engine):
    client = OllamaClient()
    base = ["contexto original"]
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[1.0, 0.0]):
        result = hybrid_context(engine, "algo sin memorias guardadas", client, base_context_chunks=base)
    assert result == base


# ----------------------------------------------------------------
# Deduplicación y pesos configurables
# ----------------------------------------------------------------
def test_does_not_duplicate_content_already_in_base_context(engine):
    mem_id = engine.save_memory(content="Mi proyecto se llama OmniLocal", memory_type="hecho", importance=0.75)
    engine.db_manager.upsert_memory_embedding(mem_id, [1.0, 0.0], "modelo-test")

    client = OllamaClient()
    base = ["Mi proyecto se llama OmniLocal"]  # ya presente, por ej. via retrieval lexico previo
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.99, 0.01]):
        result = hybrid_context(engine, "proyecto", client, base_context_chunks=base)

    assert result.count("Mi proyecto se llama OmniLocal") == 1


def test_weights_are_configurable():
    assert DEFAULT_WEIGHTS == (0.5, 0.4, 0.1)


def test_custom_weights_change_ranking(engine):
    id_a = engine.save_memory(content="El horario del taller es de 9 a 18", memory_type="hecho", importance=0.0)
    engine.db_manager.upsert_memory_embedding(id_a, [0.0, 1.0], "modelo-test")
    id_b = engine.save_memory(content="Evento sin relacion textual", memory_type="hecho", importance=1.0)
    engine.db_manager.upsert_memory_embedding(id_b, [0.0, 1.0], "modelo-test")

    client = OllamaClient()
    # Mismo semantic_score para A y B (mismo vector) -> con peso de importancia
    # alto, B (importance=1.0) debe ganarle a A (importance=0.0).
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.0, 1.0]):
        result = hybrid_context(
            engine, "consulta generica", client, base_context_chunks=[],
            weights=(0.0, 0.0, 1.0), min_semantic_similarity=0.0,
        )

    idx_a = next(i for i, c in enumerate(result) if "taller" in c)
    idx_b = next(i for i, c in enumerate(result) if "Evento" in c)
    assert idx_b < idx_a
