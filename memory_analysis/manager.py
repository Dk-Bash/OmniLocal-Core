from typing import Optional
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_analysis.models import MemoryAnalysis


class MemoryAnalysisManager:
    """
    Gestor de consolidación y análisis de memorias para OmniLocal-Core (Módulo 16).
    Analiza memorias existentes sin modificarlas y genera información estadística de diagnóstico.
    Regla arquitectónica: NO escribe SQL directo. Utiliza únicamente SQLiteManager y MemoryManager.
    """

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        db_manager: Optional[SQLiteManager] = None
    ):
        self.db_manager = db_manager or (memory_manager.db_manager if memory_manager else SQLiteManager())
        self.db_manager.create_tables()
        self.memory_manager = memory_manager or MemoryManager(db_manager=self.db_manager)

    def analyze_memory(self) -> MemoryAnalysis:
        """
        Analiza las memorias registradas en la base de datos y genera una instancia de MemoryAnalysis.
        - total_memories: Total de recuerdos almacenados.
        - memory_types: Diccionario con el conteo agrupado por tipo de memoria.
        - most_common_type: Tipo de memoria con mayor frecuencia.
        - average_importance: Promedio de la importancia de todas las memorias.
        """
        total_memories = self.db_manager.count_memories()
        memory_types = self.db_manager.count_memory_types()
        avg_importance = self.db_manager.get_average_memory_importance()

        if memory_types:
            most_common_type = max(memory_types, key=memory_types.get)
        else:
            most_common_type = "none"

        return MemoryAnalysis(
            total_memories=total_memories,
            memory_types=memory_types,
            most_common_type=most_common_type,
            average_importance=round(avg_importance, 4) if isinstance(avg_importance, float) else avg_importance
        )
