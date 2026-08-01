import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.ollama_client import OllamaClient
from local_ai.memory_detector import MemoryCandidate
from local_ai.memory_consolidation import consolidate_fact


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
# Categorías de valor único: nombre / ocupacion
# ----------------------------------------------------------------
def test_first_time_single_value_category_inserts_new(engine):
    mem_id = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))
    memories = engine.get_all_memories()
    assert len(memories) == 1
    assert memories[0].id == mem_id
    assert memories[0].content == "Nombre: Marcelo"


def test_repeating_same_value_does_nothing(engine):
    id1 = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))
    id2 = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))

    assert id1 == id2
    assert len(engine.get_all_memories()) == 1
    assert engine.db_manager.get_memory_history(id1) == []


def test_different_value_same_category_updates_in_place(engine):
    id1 = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))
    id2 = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcos"))

    assert id1 == id2  # mismo id, se actualizo, no se creo uno nuevo
    memories = engine.get_all_memories()
    assert len(memories) == 1
    assert memories[0].content == "Nombre: Marcos"


def test_update_creates_history_entry(engine):
    mem_id = consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))
    consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcos"))

    history = engine.db_manager.get_memory_history(mem_id)
    assert len(history) == 1
    assert history[0]["previous_content"] == "Nombre: Marcelo"
    assert history[0]["new_content"] == "Nombre: Marcos"


def test_ocupacion_and_nombre_are_independent_slots(engine):
    consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcelo"))
    consolidate_fact(engine, MemoryCandidate(content="Ocupacion: programador"))
    consolidate_fact(engine, MemoryCandidate(content="Nombre: Marcos"))

    memories = {m.content for m in engine.get_all_memories()}
    assert memories == {"Nombre: Marcos", "Ocupacion: programador"}


# ----------------------------------------------------------------
# Categorías de colección: proyecto / preferencia / otro
# ----------------------------------------------------------------
def test_identical_collection_item_is_not_duplicated(engine):
    id1 = consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal"))
    id2 = consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal"))

    assert id1 == id2
    assert len(engine.get_all_memories()) == 1


def test_different_collection_items_are_both_kept(engine):
    """El test que pidieron explícitamente: proyectos distintos NUNCA deben fusionarse."""
    consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal"))
    consolidate_fact(engine, MemoryCandidate(content="Proyecto: Fenix"))

    memories = engine.get_all_memories()
    assert len(memories) == 2
    contents = {m.content for m in memories}
    assert contents == {"Proyecto: OmniLocal", "Proyecto: Fenix"}
    # Ninguno debe tener historial: no hubo actualización, hubo dos hechos distintos.
    for m in memories:
        assert engine.db_manager.get_memory_history(m.id) == []


def test_similar_but_different_projects_are_not_merged_via_semantic_similarity(engine):
    """Aunque los vectores sean parecidos (proyectos relacionados pero
    distintos), si el contenido no es casi idéntico no deben fusionarse."""
    id_a = consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal Core"))
    engine.db_manager.upsert_memory_embedding(id_a, [1.0, 0.0, 0.0], "modelo-test")

    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.6, 0.8, 0.0]):  # relacionado, similitud ~0.6, no identico
        id_b = consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal Mobile"), ollama=client)

    assert id_a != id_b
    memories = engine.get_all_memories()
    assert len(memories) == 2
    contents = {m.content for m in memories}
    assert contents == {"Proyecto: OmniLocal Core", "Proyecto: OmniLocal Mobile"}


def test_near_duplicate_detected_via_high_semantic_similarity(engine):
    id_a = consolidate_fact(engine, MemoryCandidate(content="Preferencia: respuestas cortas"))
    engine.db_manager.upsert_memory_embedding(id_a, [1.0, 0.0], "modelo-test")

    client = OllamaClient()
    with patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed", return_value=[0.999, 0.001]):  # casi identico
        id_b = consolidate_fact(engine, MemoryCandidate(content="Preferencia: respuestas breves"), ollama=client)

    assert id_a == id_b
    assert len(engine.get_all_memories()) == 1


def test_collection_dedup_without_embeddings_falls_back_to_exact_match_only(engine):
    """Sin modelo de embeddings, la deduplicacion de colecciones solo
    detecta coincidencia EXACTA -- no rompe, solo es mas conservadora."""
    consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal"))
    consolidate_fact(engine, MemoryCandidate(content="Proyecto: OmniLocal (variante)"), ollama=None)

    assert len(engine.get_all_memories()) == 2  # no eran identicos, y sin embeddings no hay como saber que son parecidos


# ----------------------------------------------------------------
# Contenido sin categoría reconocida
# ----------------------------------------------------------------
def test_content_without_recognized_category_just_inserts(engine):
    mem_id = consolidate_fact(engine, MemoryCandidate(content="El wifi de casa es RedCasa123"))
    memories = engine.get_all_memories()
    assert len(memories) == 1
    assert memories[0].id == mem_id
