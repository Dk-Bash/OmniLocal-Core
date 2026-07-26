from datetime import datetime
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.models import User, Memory, Conversation
from pydantic import ValidationError

try:
    import pytest
except ImportError:
    pytest = None


def test_user_model():
    """Verifica que el modelo User pueda crearse correctamente."""
    user = User(name="Marcelo")
    assert user.id is None
    assert user.name == "Marcelo"
    assert isinstance(user.created_at, datetime)


def test_memory_model_valid_importance():
    """Verifica que Memory acepte valores de importancia válidos entre 0.0 y 1.0."""
    memory = Memory(
        content="Estoy aprendiendo Python",
        memory_type="learning",
        importance=0.8
    )
    assert memory.id is None
    assert memory.content == "Estoy aprendiendo Python"
    assert memory.memory_type == "learning"
    assert memory.importance == 0.8
    assert isinstance(memory.created_at, datetime)


def test_memory_model_invalid_importance():
    """Verifica que Memory rechace valores fuera del rango [0.0, 1.0]."""
    # Probar un valor superior a 1.0 (debe lanzar ValidationError)
    invalid_passed = False
    try:
        Memory(content="Recuerdo inválido", importance=1.5)
    except ValidationError:
        invalid_passed = True
    assert invalid_passed, "Memory no rechazó la importancia 1.5"

    # Probar un valor inferior a 0.0 (debe lanzar ValidationError)
    negative_passed = False
    try:
        Memory(content="Recuerdo inválido negativo", importance=-0.2)
    except ValidationError:
        negative_passed = True
    assert negative_passed, "Memory no rechazó la importancia -0.2"


def test_conversation_model():
    """Verifica que el modelo Conversation se cree adecuadamente."""
    conv = Conversation(
        user_input="¿Qué es OmniLocal?",
        assistant_response="Es una arquitectura de inteligencia local modular."
    )
    assert conv.id is None
    assert conv.user_input == "¿Qué es OmniLocal?"
    assert conv.assistant_response == "Es una arquitectura de inteligencia local modular."
    assert isinstance(conv.created_at, datetime)


if __name__ == "__main__":
    test_user_model()
    test_memory_model_valid_importance()
    test_memory_model_invalid_importance()
    test_conversation_model()
    print("✅ test_models.py: Todos los modelos Pydantic pasaron las pruebas correctamente.")
