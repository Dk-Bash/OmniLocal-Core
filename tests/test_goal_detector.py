from datetime import date, timedelta

from local_ai.goal_detector import (
    detect_goal_creation,
    detect_goal_update,
    find_matching_pending_goal,
)

MONDAY = date(2026, 8, 3)


# ----------------------------------------------------------------
# Creación (Bloque 9 + estructuración del Bloque 10)
# ----------------------------------------------------------------
def test_detects_recordame_que_without_date():
    result = detect_goal_creation("Recordame que compre pan")
    assert result is not None
    assert result.title == "compre pan"
    assert result.due_at is None
    assert result.goal_type == "task"
    assert result.category is None


def test_detects_recordame_without_que():
    result = detect_goal_creation("recordame llamar al dentista")
    assert result.title == "llamar al dentista"


def test_detects_acordate_de():
    result = detect_goal_creation("acordate de regar las plantas")
    assert result.title == "regar las plantas"


def test_detects_no_te_olvides_de():
    result = detect_goal_creation("no te olvides de mandar el mail")
    assert result.title == "mandar el mail"


def test_extracts_relative_date_and_cleans_title():
    result = detect_goal_creation("Recordame estudiar Linux mañana")
    assert result.title == "estudiar Linux"
    assert result.due_at is not None  # depende de la fecha real de hoy, solo confirmamos que se extrajo


def test_ignores_questions():
    assert detect_goal_creation("¿te acordás de lo que hablamos?") is None
    assert detect_goal_creation("Recordame que hora es?") is None


def test_ignores_unrelated_text():
    assert detect_goal_creation("Mi nombre es Marcelo") is None
    assert detect_goal_creation("Hola, como estas") is None


def test_ignores_empty_text():
    assert detect_goal_creation("") is None
    assert detect_goal_creation("   ") is None


# ----------------------------------------------------------------
# Actualización (Bloque 10)
# ----------------------------------------------------------------
def test_detects_update_cambiar_para():
    result = detect_goal_update("cambiar estudiar Linux para el viernes")
    assert result is not None
    assert result.reference_text == "estudiar Linux"
    assert result.new_due_at is not None


def test_detects_update_mover_para():
    result = detect_goal_update("mover la reunion para mañana")
    assert result is not None
    assert "reunion" in result.reference_text


def test_does_not_detect_update_without_explicit_reference():
    """'cambialo para el viernes' no menciona el objetivo -- no matchea ningun patron de actualizacion."""
    assert detect_goal_update("cambialo para el viernes") is None


def test_update_ignores_questions():
    assert detect_goal_update("¿podrías cambiar esto para el viernes?") is None


# ----------------------------------------------------------------
# Búsqueda del objetivo mencionado (Bloque 10)
# ----------------------------------------------------------------
def test_find_matching_pending_goal_single_candidate():
    class FakeGoal:
        def __init__(self, content):
            self.content = content
    pending = [FakeGoal("estudiar Linux"), FakeGoal("comprar pan")]
    match = find_matching_pending_goal(pending, "estudiar Linux")
    assert match is not None
    assert match.content == "estudiar Linux"


def test_find_matching_pending_goal_no_match_returns_none():
    class FakeGoal:
        def __init__(self, content):
            self.content = content
    pending = [FakeGoal("estudiar Linux")]
    assert find_matching_pending_goal(pending, "comprar leche") is None


def test_find_matching_pending_goal_ambiguous_returns_none():
    """Dos objetivos comparten palabras clave con la referencia -> ambiguo, no se adivina."""
    class FakeGoal:
        def __init__(self, content):
            self.content = content
    pending = [FakeGoal("estudiar Linux"), FakeGoal("estudiar Python")]
    assert find_matching_pending_goal(pending, "estudiar algo") is None


def test_find_matching_pending_goal_empty_list():
    assert find_matching_pending_goal([], "estudiar Linux") is None
