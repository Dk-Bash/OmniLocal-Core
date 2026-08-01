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


def test_direct_memory_match_never_calls_model(engine):
    assistant = LocalAssistant(engine=engine)
    assistant.remember("El wifi de casa es RedCasa123")

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("RedCasa123")
        mock_generate.assert_not_called()

    assert result.source == "memoria_local"
    assert result.used_model is False
    assert "RedCasa123" in result.answer


def test_no_model_available_degrades_gracefully(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=False):
        result = assistant.ask("algo que no está guardado en ningún lado")

    assert result.source == "sin_modelo"
    assert "Ollama" in result.answer


def test_model_path_saves_new_memory_for_next_time(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="La respuesta generada por el modelo."):
        result = assistant.ask("una pregunta nueva")

    assert result.source == "modelo_ia"
    assert result.used_model is True

    memories = engine.get_all_memories()
    assert any("La respuesta generada por el modelo." in m.content for m in memories)

    conversations = engine.db_manager.get_conversations()
    assert len(conversations) == 1
    assert conversations[0]["assistant_response"] == "La respuesta generada por el modelo."


def test_ask_saves_detected_fact_as_hecho_instead_of_generic_conversation(engine):
    """Bloque 1: si el usuario dice un dato reutilizable, se guarda como
    'hecho' con más peso, no como charla genérica."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="¡Encantado, Marcelo!"):
        result = assistant.ask("Mi nombre es Marcelo")

    assert result.source == "modelo_ia"

    memories = engine.get_all_memories()
    hechos = [m for m in memories if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "Marcelo" in hechos[0].content
    assert hechos[0].importance == 0.75
    # No debe haber quedado también guardado como charla genérica duplicada.
    assert not any(m.memory_type == "conversacion" for m in memories)


def test_new_declaration_is_not_masked_by_unrelated_old_memory(engine):
    """Regresión: un mensaje nuevo con datos ("mi nombre es X y trabajo en
    Y") no debe devolver una charla vieja no relacionada solo porque
    comparte alguna palabra clave (ej. "nombre"), y el dato nuevo se debe
    guardar en vez de perderse."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="hola generico, contame mas"):
        assistant.ask("Bienvenido al mundo! Mi nombre es Marcelo, y el tuyo?")

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="¡Genial que trabajes en ICQA!"):
        result = assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    # No debe haber devuelto la charla vieja como si "respondiera" al mensaje nuevo.
    assert "Bienvenido al mundo" not in result.answer

    hechos = [m for m in engine.get_all_memories() if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "ICQA" in hechos[0].content


def test_new_declaration_saved_even_without_model_available(engine):
    """El dato nuevo se guarda igual aunque no haya modelo disponible."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=False):
        result = assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    assert result.source == "memoria_local"
    hechos = [m for m in engine.get_all_memories() if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "ICQA" in hechos[0].content


def test_model_error_returns_friendly_fallback(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=OllamaUnavailableError("boom")):
        result = assistant.ask("otra pregunta nueva")

    assert result.source == "sin_modelo"
    assert result.used_model is False


def test_empty_query_is_handled():
    assistant = LocalAssistant()
    result = assistant.ask("   ")
    assert result.source == "vacio"


def test_ensure_running_returns_true_if_already_available():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=True):
        assert client.ensure_running() is True


def test_ensure_running_returns_false_if_ollama_not_installed():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=False), \
         patch("local_ai.ollama_client.shutil.which", return_value=None):
        assert client.ensure_running() is False


def test_ensure_running_starts_process_when_installed_but_stopped():
    client = OllamaClient()
    availability = iter([False, False, True])
    with patch.object(OllamaClient, "is_available", side_effect=lambda: next(availability)), \
         patch("local_ai.ollama_client.shutil.which", return_value="/usr/bin/ollama"), \
         patch("local_ai.ollama_client.subprocess.Popen") as mock_popen, \
         patch("local_ai.ollama_client.time.sleep"):
        assert client.ensure_running(wait_seconds=3) is True
        mock_popen.assert_called_once()
