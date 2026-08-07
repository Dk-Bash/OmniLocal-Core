import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from goals.manager import GoalManager
from local_ai.profile_digest import build_profile_digest, format_profile_digest_as_text


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


def test_empty_digest(setup):
    engine, goal_manager = setup
    digest = build_profile_digest(engine, goal_manager)
    assert digest["hechos_por_categoria"] == {}
    assert digest["hechos_sin_categoria"] == []
    assert digest["objetivos_pendientes"] == []


def test_groups_facts_by_category(setup):
    engine, goal_manager = setup
    engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    engine.save_memory(content="Proyecto: OmniLocal", memory_type="hecho", importance=0.75)
    engine.save_memory(content="Proyecto: Fenix", memory_type="hecho", importance=0.75)

    digest = build_profile_digest(engine, goal_manager)

    assert digest["hechos_por_categoria"]["nombre"] == ["Nombre: Marcelo"]
    assert sorted(digest["hechos_por_categoria"]["proyecto"]) == ["Proyecto: Fenix", "Proyecto: OmniLocal"]


def test_ignores_non_hecho_memories(setup):
    engine, goal_manager = setup
    engine.save_memory(content="P: algo\nR: algo mas", memory_type="conversacion", importance=0.4)

    digest = build_profile_digest(engine, goal_manager)

    assert digest["hechos_por_categoria"] == {}
    assert digest["hechos_sin_categoria"] == []


def test_facts_without_recognized_category_go_separately(setup):
    engine, goal_manager = setup
    engine.save_memory(content="El wifi de casa es RedCasa123", memory_type="hecho", importance=0.75)

    digest = build_profile_digest(engine, goal_manager)

    assert digest["hechos_por_categoria"] == {}
    assert digest["hechos_sin_categoria"] == ["El wifi de casa es RedCasa123"]


def test_includes_only_pending_goals(setup):
    engine, goal_manager = setup
    id1 = goal_manager.create_goal("Estudiar Linux")
    goal_manager.create_goal("Comprar pan")
    goal_manager.complete_goal(id1)

    digest = build_profile_digest(engine, goal_manager)

    assert digest["objetivos_pendientes"] == ["Comprar pan"]


def test_cancelled_goals_excluded(setup):
    engine, goal_manager = setup
    id1 = goal_manager.create_goal("Estudiar Linux")
    goal_manager.cancel_goal(id1)

    digest = build_profile_digest(engine, goal_manager)

    assert digest["objetivos_pendientes"] == []


# ----------------------------------------------------------------
# Formato de texto
# ----------------------------------------------------------------
def test_format_empty_digest():
    text = format_profile_digest_as_text({"hechos_por_categoria": {}, "hechos_sin_categoria": [], "objetivos_pendientes": []})
    assert "no hay" in text.lower()


def test_format_includes_all_sections():
    digest = {
        "hechos_por_categoria": {"nombre": ["Nombre: Marcelo"], "proyecto": ["Proyecto: OmniLocal"]},
        "hechos_sin_categoria": ["El wifi de casa es RedCasa123"],
        "objetivos_pendientes": ["Estudiar Linux"],
    }
    text = format_profile_digest_as_text(digest)

    assert "Nombre: Marcelo" in text
    assert "Proyecto: OmniLocal" in text
    assert "RedCasa123" in text
    assert "Estudiar Linux" in text


# ----------------------------------------------------------------
# Limite de tamano (Bloque 11C)
# ----------------------------------------------------------------
def test_format_without_max_chars_is_unaffected():
    """Default (None) sigue siendo el comportamiento original, sin recorte."""
    digest = {
        "hechos_por_categoria": {"nombre": ["Nombre: Marcelo"]},
        "hechos_sin_categoria": [],
        "objetivos_pendientes": [],
    }
    text = format_profile_digest_as_text(digest)
    assert "... (se omitieron" not in text


def test_format_truncates_when_exceeding_max_chars():
    digest = {
        "hechos_por_categoria": {"proyecto": [f"Proyecto: {i}" for i in range(50)]},
        "hechos_sin_categoria": [],
        "objetivos_pendientes": [],
    }
    text = format_profile_digest_as_text(digest, max_chars=200)
    assert len(text) <= 200
    assert "se omitieron" in text


def test_format_caps_items_per_section():
    digest = {
        "hechos_por_categoria": {"proyecto": [f"Proyecto: {i}" for i in range(50)]},
        "hechos_sin_categoria": [],
        "objetivos_pendientes": [],
    }
    text = format_profile_digest_as_text(digest, max_chars=100000)  # limite generoso, no deberia recortar por caracteres
    count = text.count("Proyecto:")
    assert count <= 15  # MAX_ITEMS_PER_SECTION
