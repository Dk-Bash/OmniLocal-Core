import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.feedback_learning import apply_feedback_to_memories, DEFAULT_DELTA


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


def _setup_conversation_with_memory(engine, importance=0.75, confidence=0.5):
    mem_id = engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=importance)
    # confidence default al guardar es 1.0 -- lo bajamos a mano para tener margen de mover en los tests
    engine.db_manager.update_memory(mem_id, "Nombre: Marcelo", confidence=confidence)
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id)
    return mem_id, conv_id


def test_useful_feedback_increases_confidence(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=0.5)

    adjusted = apply_feedback_to_memories(engine, conv_id, useful=True)

    assert adjusted == [mem_id]
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(0.5 + DEFAULT_DELTA)


def test_not_useful_feedback_decreases_confidence(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=0.5)

    adjusted = apply_feedback_to_memories(engine, conv_id, useful=False)

    assert adjusted == [mem_id]
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(0.5 - DEFAULT_DELTA)


def test_confidence_never_exceeds_upper_bound(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=0.98)

    apply_feedback_to_memories(engine, conv_id, useful=True, delta=0.05)

    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(1.0)


def test_confidence_never_goes_below_zero(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=0.02)

    apply_feedback_to_memories(engine, conv_id, useful=False, delta=0.05)

    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(0.0)


def test_already_at_bound_is_not_reported_as_adjusted(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=1.0)

    adjusted = apply_feedback_to_memories(engine, conv_id, useful=True)

    assert adjusted == []
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(1.0)


def test_does_not_touch_importance(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, importance=0.75, confidence=0.5)

    apply_feedback_to_memories(engine, conv_id, useful=True)

    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.importance == pytest.approx(0.75)  # sin cambios


def test_conversation_without_memory_usage_returns_empty(engine):
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    adjusted = apply_feedback_to_memories(engine, conv_id, useful=True)
    assert adjusted == []


def test_custom_delta_is_respected(engine):
    mem_id, conv_id = _setup_conversation_with_memory(engine, confidence=0.5)

    apply_feedback_to_memories(engine, conv_id, useful=True, delta=0.2)

    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(0.7)


def test_multiple_memories_in_same_conversation_all_adjusted(engine):
    mem_id_1 = engine.save_memory(content="Nombre: Marcelo", memory_type="hecho")
    mem_id_2 = engine.save_memory(content="Proyecto: OmniLocal", memory_type="hecho")
    engine.db_manager.update_memory(mem_id_1, "Nombre: Marcelo", confidence=0.5)
    engine.db_manager.update_memory(mem_id_2, "Proyecto: OmniLocal", confidence=0.5)
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id_1)
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id_2)

    adjusted = apply_feedback_to_memories(engine, conv_id, useful=True)

    assert sorted(adjusted) == sorted([mem_id_1, mem_id_2])
