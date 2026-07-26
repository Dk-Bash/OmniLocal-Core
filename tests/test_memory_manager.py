import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory.models import Memory


def test_memory_manager_lifecycle():
    """
    Prueba unitaria completa del ciclo de vida de MemoryManager:
    - Crear memoria y recibir ID
    - Recuperar memoria por ID
    - Obtener la lista completa de recuerdos
    - Eliminar un recuerdo y confirmar su eliminación
    """
    # Usar una base de datos de pruebas o la SQLiteManager por defecto
    sqlite_mgr = SQLiteManager()
    sqlite_mgr.connect()
    sqlite_mgr.create_tables()

    manager = MemoryManager(db_manager=sqlite_mgr)

    # 1. Crear memoria
    mem_id1 = manager.save_memory(
        content="Aprender Python",
        memory_type="learning",
        importance=0.8
    )
    assert isinstance(mem_id1, int) and mem_id1 > 0, "save_memory debe devolver un ID numérico entero positivo."

    # 2. Recuperar memoria creada
    memory1 = manager.get_memory(mem_id1)
    assert memory1 is not None, f"No se pudo recuperar la memoria con ID {mem_id1}."
    assert isinstance(memory1, Memory), "El objeto recuperado debe ser una instancia de Memory."
    assert memory1.content == "Aprender Python"
    assert memory1.memory_type == "learning"
    assert memory1.importance == 0.8

    # 3. Guardar un segundo recuerdo y obtener todas las memorias
    mem_id2 = manager.save_memory(
        content="Configurar SQLite local",
        memory_type="architecture",
        importance=0.9
    )
    all_memories = manager.get_all_memories()
    assert isinstance(all_memories, list), "get_all_memories debe devolver una lista."
    assert len(all_memories) >= 2, "La lista de recuerdos debe contener al menos 2 elementos."
    assert any(m.id == mem_id1 for m in all_memories)
    assert any(m.id == mem_id2 for m in all_memories)

    # 4. Eliminar memoria y verificar que ya no existe
    deleted = manager.delete_memory(mem_id1)
    assert deleted is True, "delete_memory debe devolver True al eliminar un ID existente."

    memory_after_delete = manager.get_memory(mem_id1)
    assert memory_after_delete is None, f"La memoria {mem_id1} debería haber sido eliminada y devolver None."

    print("✅ test_memory_manager.py: Todas las operaciones de MemoryManager pasaron exitosamente.")


if __name__ == "__main__":
    test_memory_manager_lifecycle()
