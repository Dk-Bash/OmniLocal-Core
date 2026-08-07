import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient
from local_ai.review_actions import confirm_memory, correct_memory, ignore_memory, CORRECTION_CONFIDENCE
from local_ai.feedback_learning import DEFAULT_DELTA
from local_ai.knowledge_observability import build_review_candidates


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


def _low_confidence_memory(engine, content="Preferencia: X", confidence=0.3):
    mem_id = engine.save_memory(content=content, memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, content, confidence=confidence)
    return mem_id


# ----------------------------------------------------------------
# confirm_memory
# ----------------------------------------------------------------
def test_confirm_memory_increases_confidence_by_default_delta(engine):
    mem_id = _low_confidence_memory(engine, confidence=0.3)

    ok = confirm_memory(engine, mem_id)

    assert ok is True
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(0.3 + DEFAULT_DELTA)
    assert memory.review_status == "confirmado"
    assert memory.reviewed_at is not None


def test_confirm_memory_does_not_touch_content(engine):
    mem_id = _low_confidence_memory(engine, content="Preferencia: X", confidence=0.3)
    confirm_memory(engine, mem_id)
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.content == "Preferencia: X"


def test_confirm_memory_caps_at_one(engine):
    mem_id = _low_confidence_memory(engine, confidence=0.98)
    confirm_memory(engine, mem_id, delta=0.1)
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.confidence == pytest.approx(1.0)


def test_confirm_nonexistent_memory_returns_false(engine):
    assert confirm_memory(engine, 9999) is False


# ----------------------------------------------------------------
# correct_memory
# ----------------------------------------------------------------
def test_correct_memory_updates_content_and_resets_confidence(engine):
    mem_id = _low_confidence_memory(engine, content="Nombre: Marcelo", confidence=0.3)

    ok = correct_memory(engine, mem_id, "Nombre: Marcos")

    assert ok is True
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.content == "Nombre: Marcos"
    assert memory.confidence == pytest.approx(CORRECTION_CONFIDENCE)
    assert memory.review_status == "corregido"


def test_correct_memory_leaves_history_trace(engine):
    mem_id = _low_confidence_memory(engine, content="Nombre: Marcelo", confidence=0.3)
    correct_memory(engine, mem_id, "Nombre: Marcos")

    history = engine.db_manager.get_memory_history(mem_id)
    assert len(history) == 1
    assert history[0]["previous_content"] == "Nombre: Marcelo"
    assert history[0]["new_content"] == "Nombre: Marcos"


def test_correct_nonexistent_memory_returns_false(engine):
    assert correct_memory(engine, 9999, "algo") is False


# ----------------------------------------------------------------
# ignore_memory
# ----------------------------------------------------------------
def test_ignore_memory_does_not_touch_content_or_confidence(engine):
    mem_id = _low_confidence_memory(engine, content="Preferencia: X", confidence=0.3)

    ok = ignore_memory(engine, mem_id)

    assert ok is True
    memory = engine.memory_manager.get_memory(mem_id)
    assert memory.content == "Preferencia: X"
    assert memory.confidence == pytest.approx(0.3)
    assert memory.review_status == "ignorado"


def test_ignore_nonexistent_memory_returns_false(engine):
    assert ignore_memory(engine, 9999) is False


# ----------------------------------------------------------------
# Integración con build_review_candidates
# ----------------------------------------------------------------
def test_ignored_memory_disappears_from_review_candidates(engine):
    mem_id = _low_confidence_memory(engine, confidence=0.3)
    assert len(build_review_candidates(engine)) == 1

    ignore_memory(engine, mem_id)

    assert build_review_candidates(engine) == []


def test_confirmed_memory_disappears_from_review_candidates_via_threshold(engine):
    """No hay filtro explicito para 'confirmado' -- desaparece porque confidence subio, no por chequeo de estado."""
    mem_id = _low_confidence_memory(engine, confidence=0.48)
    assert len(build_review_candidates(engine, low_confidence_threshold=0.5)) == 1

    confirm_memory(engine, mem_id, delta=0.05)  # 0.48 + 0.05 = 0.53, supera el umbral 0.5

    assert build_review_candidates(engine, low_confidence_threshold=0.5) == []


def test_corrected_memory_disappears_from_review_candidates(engine):
    mem_id = _low_confidence_memory(engine, confidence=0.3)
    correct_memory(engine, mem_id, "Preferencia: Y corregida")

    assert build_review_candidates(engine, low_confidence_threshold=0.5) == []


# ----------------------------------------------------------------
# Consistencia de punta a punta (mismo criterio pedido en el Bloque 12)
# ----------------------------------------------------------------
def test_consistency_real_flow_low_confidence_to_confirmed(engine):
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="ok"):
        assistant.ask("Mi nombre es Marcelo")

    mem = [m for m in engine.get_all_memories() if m.memory_type == "hecho"][0]
    engine.db_manager.update_memory(mem.id, mem.content, confidence=0.3)  # simula confianza baja real

    candidates_before = build_review_candidates(engine, low_confidence_threshold=0.5)
    assert any(c["id"] == mem.id for c in candidates_before)

    confirm_memory(engine, mem.id, delta=0.3)  # sube por encima del umbral

    candidates_after = build_review_candidates(engine, low_confidence_threshold=0.5)
    assert not any(c["id"] == mem.id for c in candidates_after)
