from typing import List, Optional
from app.config import PROJECT_NAME, VERSION
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory.models import Memory


class OmniLocalEngine:
    """
    Clase núcleo para OmniLocal-Core.
    Coordina la inicialización, el estado del motor y delega las operaciones de memoria
    a través de MemoryManager y SQLiteManager sin escribir SQL directamente.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.name = PROJECT_NAME
        self.version = VERSION
        self.is_running = False

        if db_manager is None:
            self.db_manager = SQLiteManager()
            self.db_manager.connect()
            self.db_manager.create_tables()
        else:
            self.db_manager = db_manager

        self.memory_manager = MemoryManager(db_manager=self.db_manager)

    def start(self) -> bool:
        """Inicia el motor de OmniLocal-Core."""
        self.is_running = True
        return True

    def status(self) -> dict:
        """Devuelve el estado actual del motor."""
        return {
            "name": self.name,
            "version": self.version,
            "running": self.is_running,
            "status": "ready" if self.is_running else "stopped",
        }

    def save_memory(self, content: str, memory_type: str = "episodic", importance: float = 0.5) -> int:
        """
        Delega el guardado de un recuerdo a MemoryManager.
        Devuelve el ID asignado al recuerdo en SQLite.
        """
        return self.memory_manager.save_memory(
            content=content,
            memory_type=memory_type,
            importance=importance
        )

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """
        Delega la búsqueda de un recuerdo por ID a MemoryManager.
        Devuelve una instancia de Memory o None si no existe.
        """
        return self.memory_manager.get_memory(memory_id)

    def get_all_memories(self) -> List[Memory]:
        """
        Delega la obtención de todos los recuerdos almacenados a MemoryManager.
        Devuelve una lista de instancias de Memory.
        """
        return self.memory_manager.get_all_memories()
