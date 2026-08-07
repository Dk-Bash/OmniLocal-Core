import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from goals.manager import GoalManager
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient
from local_ai.knowledge_observability import (
    build_memory_insights,
    build_goal_insights,
    build_review_candidates,
)


@pytest.fixture
def setup():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    engine = OmniLocalEngine(db_manager=db_manager)
    engine.start()
    goal_manager = GoalManager(db_manager=db_manager)
    yield engine, goal_manager
    db_manager.close()
    os.remove(path)


# ----------------------------------------------------------------
# Parte 1 -- Memory Insights
# ----------------------------------------------------------------
def test_total_por_tipo(setup):
    engine, goal_manager = setup
    engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    engine.save_memory(content="P: x\nR: y", memory_type="conversacion", importance=0.4)

    insights = build_memory_insights(engine)
    assert insights["total_por_tipo"] == {"hecho": 1, "conversacion": 1}


def test_confianza_baja(setup):
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Preferencia: X", memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, "Preferencia: X", confidence=0.35)

    insights = build_memory_insights(engine, low_confidence_threshold=0.5)
    assert len(insights["confianza_baja"]) == 1
    assert insights["confianza_baja"][0]["confidence"] == 0.35


def test_nunca_usadas(setup):
    engine, goal_manager = setup
    engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)

    insights = build_memory_insights(engine)
    assert len(insights["nunca_usadas"]) == 1


def test_sin_uso_reciente(setup):
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id)
    conn = engine.db_manager.connect()
    conn.execute("UPDATE conversation_memory_usage SET created_at = ? WHERE memory_id = ?;", (old_date, mem_id))
    conn.commit()

    insights = build_memory_insights(engine, unused_days_threshold=180)
    assert len(insights["sin_uso_reciente"]) == 1
    assert insights["sin_uso_reciente"][0]["dias_sin_uso"] >= 180


def test_uso_reciente_no_aparece_como_sin_uso(setup):
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id)

    insights = build_memory_insights(engine, unused_days_threshold=180)
    assert insights["sin_uso_reciente"] == []
    assert insights["nunca_usadas"] == []


def test_mas_modificadas_ordenadas_por_cantidad_de_cambios(setup):
    engine, goal_manager = setup
    id1 = engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    id2 = engine.save_memory(content="Ocupacion: X", memory_type="hecho", importance=0.75)
    engine.db_manager.insert_memory_history(id1, "a", "b")
    engine.db_manager.insert_memory_history(id1, "b", "c")
    engine.db_manager.insert_memory_history(id2, "x", "y")

    insights = build_memory_insights(engine)
    assert insights["mas_modificadas"][0]["change_count"] == 2


def test_conversacion_memories_excluded_from_confidence_and_usage_signals(setup):
    engine, goal_manager = setup
    engine.save_memory(content="P: x\nR: y", memory_type="conversacion", importance=0.4)

    insights = build_memory_insights(engine)
    assert insights["confianza_baja"] == []
    assert insights["nunca_usadas"] == []


# ----------------------------------------------------------------
# Parte 2 -- Goal Insights
# ----------------------------------------------------------------
def test_goal_insights_vencido(setup):
    engine, goal_manager = setup
    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    goal_manager.create_goal("Tarea vieja", due_at=past_date)

    insights = build_goal_insights(engine, goal_manager)
    assert insights["pendientes_actuales"] == 1
    assert len(insights["vencidos"]) == 1


def test_goal_insights_no_vencido(setup):
    engine, goal_manager = setup
    future_date = (datetime.now() + timedelta(days=5)).isoformat()
    goal_manager.create_goal("Tarea futura", due_at=future_date)

    insights = build_goal_insights(engine, goal_manager)
    assert insights["vencidos"] == []


def test_goal_insights_sin_modificaciones_recientes(setup):
    engine, goal_manager = setup
    goal_id = goal_manager.create_goal("Tarea")
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    conn = engine.db_manager.connect()
    conn.execute("UPDATE goals SET created_at = ? WHERE id = ?;", (old_date, goal_id))
    conn.commit()

    insights = build_goal_insights(engine, goal_manager, stale_days_threshold=120)
    assert len(insights["sin_modificaciones_recientes"]) == 1


def test_goal_update_sets_updated_at_and_resets_staleness(setup):
    """El cambio a update_goal() del Bloque 12: actualizar un objetivo deja rastro en updated_at."""
    engine, goal_manager = setup
    goal_id = goal_manager.create_goal("Tarea")
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    conn = engine.db_manager.connect()
    conn.execute("UPDATE goals SET created_at = ? WHERE id = ?;", (old_date, goal_id))
    conn.commit()

    insights_before = build_goal_insights(engine, goal_manager, stale_days_threshold=120)
    assert len(insights_before["sin_modificaciones_recientes"]) == 1

    goal_manager.update_goal(goal_id, content="Tarea actualizada")
    updated_goal = goal_manager.get_goal(goal_id)
    assert updated_goal.updated_at is not None

    insights_after = build_goal_insights(engine, goal_manager, stale_days_threshold=120)
    assert insights_after["sin_modificaciones_recientes"] == []


# ----------------------------------------------------------------
# Parte 3 -- Review Candidates (sin score combinado)
# ----------------------------------------------------------------
def test_review_candidates_lists_reasons_separately(setup):
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Preferencia: X", memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, "Preferencia: X", confidence=0.3)

    candidates = build_review_candidates(engine, low_confidence_threshold=0.5)
    assert len(candidates) == 1
    assert "confianza baja" in candidates[0]["reasons"][0]


def test_review_candidates_never_has_combined_score_field(setup):
    """Confirmacion explicita pedida en la auditoria: los resultados reales
    nunca traen un campo de score/salud combinado -- 'id', 'content' y
    'reasons' (motivos separados). Bloque 13: se agrego 'id' a proposito
    para poder actuar sobre un candidato (antes solo tenia content/reasons)."""
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Preferencia: X", memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, "Preferencia: X", confidence=0.3)

    candidates = build_review_candidates(engine, low_confidence_threshold=0.5)
    assert len(candidates) == 1
    assert set(candidates[0].keys()) == {"id", "content", "reasons"}
    assert candidates[0]["id"] == mem_id
    for candidate in candidates:
        assert "score" not in candidate
        assert "salud" not in candidate


def test_review_candidates_multiple_reasons_for_same_memory(setup):
    engine, goal_manager = setup
    mem_id = engine.save_memory(content="Preferencia: X", memory_type="hecho", importance=0.75)
    engine.db_manager.update_memory(mem_id, "Preferencia: X", confidence=0.2)
    conv_id = engine.db_manager.insert_conversation(user_input="q", assistant_response="a")
    engine.db_manager.insert_conversation_memory_usage(conv_id, mem_id)
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    conn = engine.db_manager.connect()
    conn.execute("UPDATE conversation_memory_usage SET created_at = ? WHERE memory_id = ?;", (old_date, mem_id))
    conn.commit()

    candidates = build_review_candidates(engine, low_confidence_threshold=0.5, unused_days_threshold=180)
    assert len(candidates) == 1
    assert len(candidates[0]["reasons"]) == 2


# ----------------------------------------------------------------
# Tests de consistencia entre memoria y observabilidad (pedido explícito
# de la aprobación) -- a través del flujo real de assistant.ask(), no
# armados a mano.
# ----------------------------------------------------------------
def test_consistency_usage_reflects_real_conversation(setup):
    engine, goal_manager = setup
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="ok"):
        assistant.ask("Mi nombre es Marcelo")

    mem = [m for m in engine.get_all_memories() if m.memory_type == "hecho"][0]

    assistant.ask("Nombre: Marcelo")

    insights = build_memory_insights(engine)
    usage_summary = engine.db_manager.get_memory_usage_summary()
    assert mem.id in usage_summary
    assert usage_summary[mem.id]["usage_count"] >= 1
    assert usage_summary[mem.id]["last_used_at"] is not None
    assert not any(item["content"] == mem.content for item in insights["nunca_usadas"])


def test_consistency_change_count_reflects_real_update(setup):
    engine, goal_manager = setup
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="ok"):
        assistant.ask("Mi nombre es Marcelo")
        assistant.ask("Mi nombre es Marcos")

    mem = engine.get_all_memories()[0]
    assert mem.content == "Nombre: Marcos"

    change_counts = engine.db_manager.get_memory_change_counts()
    assert change_counts.get(mem.id) == 1

    insights = build_memory_insights(engine)
    assert any(item["content"] == "Nombre: Marcos" and item["change_count"] == 1 for item in insights["mas_modificadas"])
