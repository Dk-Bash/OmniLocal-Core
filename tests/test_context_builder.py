import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.context_builder import build_context, DEFAULT_MAX_TURNS


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


def _new_session(engine, title="Charla"):
    return engine.db_manager.insert_chat_session(title)


# ----------------------------------------------------------------
# Caso 1: continuidad dentro de una misma sesión
# ----------------------------------------------------------------
def test_context_includes_previous_turn_of_same_session(engine):
    session_id = _new_session(engine)
    engine.db_manager.insert_conversation(
        user_input="Estoy desarrollando un asistente local",
        assistant_response="Suena interesante, ¿qué tecnologías usás?",
        session_id=session_id,
    )

    context = build_context(engine, "Quiero agregarle memoria", session_id=session_id)

    assert any("asistente local" in c for c in context)


def test_context_without_session_id_has_no_conversation_history(engine):
    context = build_context(engine, "cualquier pregunta", session_id=None)
    # Sin session_id no debe haber memoria corta -- solo lo que aporte retrieval (nada guardado acá).
    assert context == []


def test_context_respects_max_turns(engine):
    session_id = _new_session(engine)
    for i in range(10):
        engine.db_manager.insert_conversation(
            user_input=f"mensaje numero {i}",
            assistant_response=f"respuesta numero {i}",
            session_id=session_id,
        )

    context = build_context(engine, "algo", session_id=session_id, max_turns=3, max_chars=100000)
    turn_chunks = [c for c in context if c.startswith("Usuario:")]
    assert len(turn_chunks) == 3
    # Deben ser los ULTIMOS 3 turnos (7, 8, 9), no los primeros.
    assert any("numero 9" in c for c in turn_chunks)
    assert any("numero 8" in c for c in turn_chunks)
    assert any("numero 7" in c for c in turn_chunks)
    assert not any("numero 0" in c for c in turn_chunks)


# ----------------------------------------------------------------
# Caso 2: aislamiento entre sesiones
# ----------------------------------------------------------------
def test_sessions_do_not_leak_into_each_other(engine):
    session_a = _new_session(engine, "Sesion A")
    session_b = _new_session(engine, "Sesion B")

    engine.db_manager.insert_conversation(
        user_input="El codigo secreto es AZUL7",
        assistant_response="Anotado.",
        session_id=session_a,
    )

    context_b = build_context(engine, "cual era el codigo", session_id=session_b)
    assert not any("AZUL7" in c for c in context_b)

    context_a = build_context(engine, "cual era el codigo", session_id=session_a)
    assert any("AZUL7" in c for c in context_a)


# ----------------------------------------------------------------
# Caso 3: límite de tamaño y descarte de mensajes antiguos
# ----------------------------------------------------------------
def test_truncation_drops_oldest_turns_first(engine):
    session_id = _new_session(engine)
    engine.db_manager.insert_conversation(
        user_input="mensaje viejo unico e irrepetible",
        assistant_response="ok",
        session_id=session_id,
    )
    engine.db_manager.insert_conversation(
        user_input="mensaje nuevo unico e irrepetible",
        assistant_response="ok",
        session_id=session_id,
    )

    # Presupuesto de caracteres chico: solo entra uno de los dos turnos.
    context = build_context(
        engine, "algo", session_id=session_id, max_turns=DEFAULT_MAX_TURNS, max_chars=60
    )

    combined = " ".join(context)
    assert "mensaje nuevo" in combined
    assert "mensaje viejo" not in combined


def test_truncation_never_exceeds_budget(engine):
    session_id = _new_session(engine)
    for i in range(20):
        engine.db_manager.insert_conversation(
            user_input=f"texto de relleno numero {i} " * 5,
            assistant_response="ok",
            session_id=session_id,
        )

    context = build_context(engine, "algo", session_id=session_id, max_turns=20, max_chars=500)
    total_len = sum(len(c) for c in context)
    assert total_len <= 500


def test_truncation_with_zero_budget_returns_empty(engine):
    session_id = _new_session(engine)
    engine.db_manager.insert_conversation(user_input="hola", assistant_response="hola", session_id=session_id)

    context = build_context(engine, "algo", session_id=session_id, max_chars=0)
    assert context == []


# ----------------------------------------------------------------
# Combinación con retrieval (memoria larga) ya existente
# ----------------------------------------------------------------
def test_context_combines_session_history_with_long_term_memory(engine):
    session_id = _new_session(engine)
    engine.save_memory(content="El horario del taller es de 9 a 18", memory_type="hecho", importance=0.8)
    engine.db_manager.insert_conversation(
        user_input="estoy armando el cronograma del taller",
        assistant_response="dale, contame mas",
        session_id=session_id,
    )

    context = build_context(engine, "horario del taller", session_id=session_id)

    assert any("9 a 18" in c for c in context)  # memoria larga (retrieval)
    assert any("cronograma del taller" in c for c in context)  # memoria corta (sesion)
