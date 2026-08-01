from unittest.mock import patch

from local_ai.memory_detector import (
    MemoryCandidate,
    detect_by_rules,
    detect_by_model,
    detect_memory_candidate,
)
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError


# ----------------------------------------------------------------
# Camino de reglas (sin modelo)
# ----------------------------------------------------------------
def test_rule_detects_name():
    candidate = detect_by_rules("Mi nombre es Marcelo")
    assert candidate is not None
    assert candidate.memory_type == "hecho"
    assert "Marcelo" in candidate.content
    assert candidate.importance == 0.75


def test_rule_detects_me_llamo_variant():
    candidate = detect_by_rules("Hola, me llamo Marcelo y quiero preguntarte algo")
    assert candidate is not None
    assert "Marcelo" in candidate.content


def test_rule_detects_occupation():
    candidate = detect_by_rules("Trabajo como programador en una empresa de software")
    assert candidate is not None
    assert "programador" in candidate.content.lower()


def test_rule_detects_project_name():
    candidate = detect_by_rules("Mi proyecto se llama OmniLocal")
    assert candidate is not None
    assert "OmniLocal" in candidate.content


def test_rule_detects_preference():
    candidate = detect_by_rules("Prefiero respuestas cortas y directas")
    assert candidate is not None
    assert "respuestas cortas" in candidate.content.lower()


def test_rule_ignores_questions():
    assert detect_by_rules("¿Cómo te llamás?") is None
    assert detect_by_rules("Como funciona esto?") is None
    assert detect_by_rules("Cual es la capital de Francia") is None


def test_rule_ignores_long_input():
    long_text = "Mi nombre es Marcelo. " + ("Y además te cuento una historia larga. " * 20)
    assert detect_by_rules(long_text) is None


def test_rule_ignores_empty_and_unrelated_text():
    assert detect_by_rules("") is None
    assert detect_by_rules("   ") is None
    assert detect_by_rules("Hola, ¿qué tal?") is None
    assert detect_by_rules("Gracias por la ayuda") is None


# ----------------------------------------------------------------
# Camino con modelo
# ----------------------------------------------------------------
def test_model_path_parses_valid_classification():
    client = OllamaClient()
    with patch.object(OllamaClient, "generate", return_value="nombre: Marcelo") as mock_gen:
        candidate = detect_by_model("Mi nombre es Marcelo", client)
    assert candidate is not None
    assert candidate.content == "Nombre: Marcelo"
    assert candidate.memory_type == "hecho"
    mock_gen.assert_called_once()


def test_model_path_returns_none_when_model_says_nada():
    client = OllamaClient()
    with patch.object(OllamaClient, "generate", return_value="NADA"):
        assert detect_by_model("¿Qué hora es?", client) is None


def test_model_path_returns_none_on_malformed_response():
    client = OllamaClient()
    with patch.object(OllamaClient, "generate", return_value="esto no tiene el formato esperado"):
        assert detect_by_model("Mi nombre es Marcelo", client) is None


def test_model_path_returns_none_on_unknown_category():
    client = OllamaClient()
    with patch.object(OllamaClient, "generate", return_value="categoria_rara: algo"):
        assert detect_by_model("texto cualquiera", client) is None


def test_model_path_returns_none_when_unavailable():
    client = OllamaClient()
    with patch.object(OllamaClient, "generate", side_effect=OllamaUnavailableError("no server")):
        assert detect_by_model("Mi nombre es Marcelo", client) is None


# ----------------------------------------------------------------
# Punto de entrada combinado
# ----------------------------------------------------------------
def test_detect_memory_candidate_prefers_model_when_available():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="proyecto: OmniLocal") as mock_gen:
        candidate = detect_memory_candidate("che, arranqué un proyecto que se llama OmniLocal", ollama=client)
    assert candidate is not None
    assert "OmniLocal" in candidate.content
    mock_gen.assert_called_once()


def test_detect_memory_candidate_falls_back_to_rules_when_model_says_nada():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="NADA"):
        candidate = detect_memory_candidate("Mi nombre es Marcelo", ollama=client)
    # El modelo dijo NADA, pero las reglas igual encuentran el patrón conocido.
    assert candidate is not None
    assert "Marcelo" in candidate.content


def test_detect_memory_candidate_falls_back_to_rules_when_model_unavailable():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=False):
        candidate = detect_memory_candidate("Mi nombre es Marcelo", ollama=client)
    assert candidate is not None
    assert "Marcelo" in candidate.content


def test_detect_memory_candidate_without_ollama_client_uses_rules():
    candidate = detect_memory_candidate("Mi nombre es Marcelo", ollama=None)
    assert candidate is not None
    assert "Marcelo" in candidate.content


def test_detect_memory_candidate_returns_none_for_plain_question():
    candidate = detect_memory_candidate("¿Cómo estás?", ollama=None)
    assert candidate is None


def test_detect_memory_candidate_handles_empty_input():
    assert detect_memory_candidate("", ollama=None) is None
    assert detect_memory_candidate("   ", ollama=None) is None


def test_detect_memory_candidate_never_raises_on_unexpected_model_error():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=RuntimeError("boom inesperado")):
        # No debe romper: cae al camino de reglas en vez de propagar la excepción.
        candidate = detect_memory_candidate("Mi nombre es Marcelo", ollama=client)
    assert candidate is not None
    assert "Marcelo" in candidate.content


def test_memory_candidate_defaults():
    candidate = MemoryCandidate(content="Nombre: Marcelo")
    assert candidate.memory_type == "hecho"
    assert candidate.importance == 0.75
