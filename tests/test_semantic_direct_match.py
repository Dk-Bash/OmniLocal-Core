import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError


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


def _save_hecho(engine, content, confidence=1.0, vector=(1.0, 0.0)):
    mem_id = engine.save_memory(content=content, memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, content, confidence=confidence)
    engine.db_manager.upsert_memory_embedding(mem_id, list(vector), "modelo-test")
    return mem_id


def test_fires_for_question_with_high_similarity_allowed_category(engine):
    _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.98, 0.02]):
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi nombre?", client)
    assert result == "Nombre: Marcelo"


def test_does_not_fire_for_declarative_text_even_with_perfect_similarity(engine):
    """La protección más importante: una declaración nunca dispara esto, aunque sea identica semánticamente."""
    _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[1.0, 0.0]):  # identico
        result = LocalAssistant._find_semantic_direct_match(engine, "Ahora mi nombre es Marcos", client)
    assert result is None


def test_does_not_fire_for_collection_categories(engine):
    _save_hecho(engine, "Proyecto: OmniLocal", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.99, 0.01]):
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi proyecto?", client)
    assert result is None


def test_does_not_fire_below_confidence_threshold(engine):
    _save_hecho(engine, "Ocupacion: programador", confidence=0.45, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.99, 0.01]):
        result = LocalAssistant._find_semantic_direct_match(engine, "¿En qué trabajo?", client)
    assert result is None


def test_does_not_fire_below_similarity_threshold(engine):
    _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.6, 0.8]):  # similitud baja
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi nombre?", client)
    assert result is None


def test_does_not_call_embed_without_embedding_model(engine):
    _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=False), \
         patch.object(OllamaClient, "embed") as mock_embed:
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi nombre?", client)
    mock_embed.assert_not_called()
    assert result is None


def test_gracefully_returns_none_on_ollama_error(engine):
    _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", side_effect=OllamaUnavailableError("boom")):
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi nombre?", client)
    assert result is None


def test_contradiction_case_rule_candidate_beats_semantic_direct_match(engine):
    """Caso pedido explícitamente en la aprobación: existe 'Nombre: Marcelo'
    con confidence alta. El usuario declara 'Mi nombre es Marcos'. Debe
    pasar por rule_candidate -> consolidate_fact -> update, y NUNCA por
    _find_semantic_direct_match (que devolvería la respuesta vieja)."""
    from local_ai.assistant import LocalAssistant
    from unittest.mock import patch as mock_patch

    assistant = LocalAssistant(engine=engine)
    mem_id = _save_hecho(engine, "Nombre: Marcelo", confidence=0.9, vector=(1.0, 0.0))

    with mock_patch.object(OllamaClient, "is_available", return_value=True), \
         mock_patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         mock_patch.object(OllamaClient, "embed", return_value=[1.0, 0.0]), \
         mock_patch.object(LocalAssistant, "_find_semantic_direct_match") as mock_semantic:
        result = assistant.ask("Mi nombre es Marcos")

    mock_semantic.assert_not_called()
    assert result.source == "memoria_local"
    assert "Marcos" in result.answer

    memories = engine.get_all_memories()
    hechos = [m for m in memories if m.memory_type == "hecho"]
    assert len(hechos) == 1  # se actualizó en el lugar, no se creó una segunda fila
    assert hechos[0].id == mem_id
    assert hechos[0].content == "Nombre: Marcos"

    history = engine.db_manager.get_memory_history(mem_id)
    assert len(history) == 1
    assert history[0]["previous_content"] == "Nombre: Marcelo"
    assert history[0]["new_content"] == "Nombre: Marcos"


def test_ignores_non_hecho_memories(engine):
    mem_id = engine.save_memory(content="Nombre: Marcelo", memory_type="conversacion", importance=0.4)
    engine.db_manager.upsert_memory_embedding(mem_id, [1.0, 0.0], "modelo-test")
    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.99, 0.01]):
        result = LocalAssistant._find_semantic_direct_match(engine, "¿Cuál es mi nombre?", client)
    assert result is None
