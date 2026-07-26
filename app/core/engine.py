from typing import List, Optional
from app.config import PROJECT_NAME, VERSION
from app.logger import get_logger
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory.models import Memory

logger = get_logger(__name__)


class OmniLocalEngine:
    """
    Clase núcleo para OmniLocal-Core.
    Coordina la inicialización, el estado del motor y delega las operaciones de memoria
    a través de MemoryManager y SQLiteManager sin escribir SQL directamente.
    Incluye logging estructurado y manejo controlled de errores.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.name = PROJECT_NAME
        self.version = VERSION
        self.is_running = False

        try:
            logger.info(f"Inicializando {self.name} v{self.version}...")
            if db_manager is None:
                self.db_manager = SQLiteManager()
                self.db_manager.connect()
                self.db_manager.create_tables()
            else:
                self.db_manager = db_manager

            self.memory_manager = MemoryManager(db_manager=self.db_manager)
            logger.info("OmniLocalEngine e componentes de memoria inicializados con éxito.")
        except Exception as e:
            logger.error(f"Error al inicializar OmniLocalEngine: {e}", exc_info=True)
            raise e

    def start(self) -> bool:
        """Inicia el motor de OmniLocal-Core."""
        try:
            self.is_running = True
            logger.info(f"{self.name} iniciado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar {self.name}: {e}")
            return False

    def status(self) -> dict:
        """Devuelve el estado actual del motor."""
        current_status = "ready" if self.is_running else "stopped"
        logger.debug(f"Consulta de estado del motor: {current_status}")
        return {
            "name": self.name,
            "version": self.version,
            "running": self.is_running,
            "status": current_status,
        }

    def save_memory(self, content: str, memory_type: str = "episodic", importance: float = 0.5) -> int:
        """
        Delega el guardado de un recuerdo a MemoryManager.
        Maneja errores de validación o persistencia de forma controlada.
        """
        try:
            logger.info(f"Guardando recuerdo de tipo '{memory_type}' con importancia {importance}...")
            mem_id = self.memory_manager.save_memory(
                content=content,
                memory_type=memory_type,
                importance=importance
            )
            logger.info(f"Recuerdo guardado exitosamente con ID: {mem_id}")
            return mem_id
        except ValueError as ve:
            logger.warning(f"Error de validación al guardar recuerdo: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Error inesperado al guardar recuerdo: {e}", exc_info=True)
            raise e

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """
        Delega la búsqueda de un recuerdo por ID a MemoryManager.
        Maneja errores o IDs inválidos de forma controlada.
        """
        try:
            if not isinstance(memory_id, int) or memory_id <= 0:
                logger.warning(f"ID de memoria inválido proporcionado: {memory_id}")
                return None

            logger.info(f"Buscando recuerdo con ID: {memory_id}")
            memory = self.memory_manager.get_memory(memory_id)
            if memory:
                logger.info(f"Recuerdo ID {memory_id} recuperado.")
            else:
                logger.info(f"Recuerdo ID {memory_id} no fue encontrado.")
            return memory
        except Exception as e:
            logger.error(f"Error al obtener recuerdo ID {memory_id}: {e}", exc_info=True)
            return None

    def get_all_memories(self) -> List[Memory]:
        """
        Delega la obtención de todos los recuerdos almacenados a MemoryManager.
        Devuelve una lista de instancias de Memory o lista vacía si ocurre un error.
        """
        try:
            logger.info("Obteniendo lista de todos los recuerdos...")
            memories = self.memory_manager.get_all_memories()
            logger.info(f"Se recuperaron {len(memories)} recuerdos.")
            return memories
        except Exception as e:
            logger.error(f"Error al listar recuerdos: {e}", exc_info=True)
            return []
