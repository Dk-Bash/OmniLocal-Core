import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine
from memory.models import Memory


def test_core_engine_integration():
    """
    Prueba unitaria para verificar la integración entre OmniLocalEngine,
    MemoryManager y SQLiteManager en el Módulo 5.
    """
    # 1. Inicialización del motor
    engine = OmniLocalEngine()
    assert engine is not None, "OmniLocalEngine debe instanciarse correctamente."
    assert engine.is_running is False, "El motor debe comenzar detenido por defecto."

    # Iniciar motor y verificar estado
    engine.start()
    assert engine.is_running is True, "engine.start() debe establecer is_running en True."

    status = engine.status()
    assert isinstance(status, dict)
    assert status["status"] == "ready"
    assert status["running"] is True

    # 2. Guardar un recuerdo a través del Core Engine
    mem_id = engine.save_memory(
        content="Aprendiendo OmniLocal",
        memory_type="project",
        importance=0.9
    )
    assert isinstance(mem_id, int) and mem_id > 0, "engine.save_memory debe retornar un ID numérico entero positivo."

    # 3. Recuperar el recuerdo a través del Core Engine
    retrieved_memory = engine.get_memory(mem_id)
    assert retrieved_memory is not None, f"No se pudo obtener la memoria con ID {mem_id}."
    assert isinstance(retrieved_memory, Memory), "El objeto retornado debe ser una instancia de Memory."
    assert retrieved_memory.content == "Aprendiendo OmniLocal"
    assert retrieved_memory.memory_type == "project"
    assert retrieved_memory.importance == 0.9

    # 4. Listar todas las memorias
    all_memories = engine.get_all_memories()
    assert isinstance(all_memories, list), "engine.get_all_memories debe devolver una lista."
    assert len(all_memories) >= 1, "La lista debe contener al menos 1 elemento."
    assert any(m.id == mem_id for m in all_memories), "El recuerdo creado debe estar presente en la lista."

    print("✅ test_core_engine.py: Pruebas de integración de OmniLocalEngine pasadas exitosamente.")


if __name__ == "__main__":
    test_core_engine_integration()
