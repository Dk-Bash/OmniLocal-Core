import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from knowledge.manager import KnowledgeManager
from retrieval.engine import RetrievalEngine
from retrieval.textutils import extract_keywords
from local_ai.assistant import LocalAssistant
from app.core.engine import OmniLocalEngine


@pytest.fixture
def retrieval_engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    memory_manager = MemoryManager(db_manager=db_manager)
    knowledge_manager = KnowledgeManager(db_manager=db_manager)
    yield RetrievalEngine(memory_manager=memory_manager, knowledge_manager=knowledge_manager)
    db_manager.close()
    os.remove(path)


def test_extract_keywords_drops_stopwords_and_short_words():
    keywords = extract_keywords("¿Cómo me llamo yo? Decime cual es mi nombre.")
    assert "nombre" in keywords
    assert "decime" in keywords
    assert "como" not in keywords  # stopword
    assert "yo" not in keywords    # muy corta


def test_paraphrased_question_finds_stored_answer_by_keyword_overlap(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(
        content="Mi nombre es Marcelo, y el tuyo?",
        memory_type="conversacion",
        importance=0.5,
    )

    # Antes del fix, esto no encontraba nada: ninguna frase completa coincide.
    results = retrieval_engine.search("Decime cual es mi nombre")
    assert len(results) >= 1
    assert any("Marcelo" in r.content for r in results)
    assert results[0].score > 0


def test_no_overlap_returns_no_results(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(
        content="Mi nombre es Marcelo",
        memory_type="conversacion",
        importance=0.5,
    )
    # Sinónimo sin ninguna palabra compartida: honestamente, no hay forma de
    # encontrarlo con búsqueda por palabras clave (haría falta comprensión
    # semántica real). Confirma que el sistema no inventa falsos positivos.
    results = retrieval_engine.search("Como me llamo yo")
    assert results == []


def test_results_ranked_by_keyword_overlap(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(content="El horario del taller es de 9 a 18", memory_type="hecho")
    retrieval_engine.memory_manager.save_memory(content="El horario de la pileta es libre", memory_type="hecho")

    results = retrieval_engine.search_memory("horario del taller")
    assert len(results) == 2
    # El que comparte más palabras clave ("horario", "taller") debe ir primero.
    assert "taller" in results[0].content


def test_assistant_uses_partial_match_as_rag_context(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    engine = OmniLocalEngine(db_manager=db_manager)
    engine.start()
    engine.save_memory(content="Mi nombre es Marcelo, y el tuyo?", memory_type="conversacion", importance=0.4)

    assistant = LocalAssistant(engine=engine)
    monkeypatch.setattr(assistant.ollama, "ensure_running", lambda: True)
    monkeypatch.setattr(assistant.ollama, "generate", lambda **kwargs: "Te llamás Marcelo.")

    result = assistant.ask("Decime cual es mi nombre")
    assert result.source == "modelo_ia"
    assert any("Marcelo" in c for c in result.context_used)

    db_manager.close()
    os.remove(path)
