import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from knowledge.manager import KnowledgeManager
from retrieval.engine import RetrievalEngine


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


def test_higher_importance_ranks_first_with_equal_keyword_overlap(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(
        content="El proyecto se llama Aurora", memory_type="hecho", importance=0.2
    )
    retrieval_engine.memory_manager.save_memory(
        content="El proyecto se llama OmniLocal", memory_type="hecho", importance=0.9
    )

    results = retrieval_engine.search_memory("proyecto se llama")

    assert len(results) == 2
    # Misma cantidad de palabras clave coincidentes en ambas ("proyecto",
    # "llama") -> debe ganar la de mayor importancia.
    assert "OmniLocal" in results[0].content
    assert "Aurora" in results[1].content
    assert results[0].score > results[1].score


def test_zero_importance_never_zeroes_the_score(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(
        content="El horario del taller es de 9 a 18", memory_type="hecho", importance=0.0
    )

    results = retrieval_engine.search_memory("horario del taller")

    assert len(results) == 1
    # Aunque la importancia sea minima, con coincidencia real de palabras
    # clave el score nunca debe caer a 0 (evita falsos "sin resultados").
    assert results[0].score > 0


def test_max_importance_gives_maximum_score_for_full_keyword_match(retrieval_engine):
    retrieval_engine.memory_manager.save_memory(
        content="El horario del taller es de 9 a 18", memory_type="hecho", importance=1.0
    )

    results = retrieval_engine.search_memory("horario del taller")

    assert len(results) == 1
    # Coincidencia completa de palabras clave (score base 1.0) + importancia
    # maxima -> debe llegar al score maximo posible (1.0).
    assert results[0].score == pytest.approx(1.0)


def test_equal_importance_still_ranks_by_keyword_overlap(retrieval_engine):
    """Reconfirma, con la nueva formula, el comportamiento del Bloque anterior:
    a igual importancia, gana quien comparte mas palabras clave."""
    retrieval_engine.memory_manager.save_memory(
        content="El horario del taller es de 9 a 18", memory_type="hecho", importance=0.5
    )
    retrieval_engine.memory_manager.save_memory(
        content="El horario de la pileta es libre", memory_type="hecho", importance=0.5
    )

    results = retrieval_engine.search_memory("horario del taller")

    assert "taller" in results[0].content


def test_knowledge_search_score_unaffected_by_ranking_change(retrieval_engine):
    """Bloque 3 no toca conocimiento: el score de knowledge sigue siendo
    puramente por superposicion de palabras clave (KnowledgeNode no tiene
    campo de importancia)."""
    retrieval_engine.knowledge_manager.create_node(
        name="OmniLocal", node_type="documento_local", description="Proyecto de IA local"
    )

    results = retrieval_engine.search_knowledge("proyecto IA local")
    assert len(results) == 1
    assert results[0].score == pytest.approx(1.0)  # 3/3 palabras clave, sin ponderacion adicional
