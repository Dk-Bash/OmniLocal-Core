from typing import Optional
from database.sqlite_manager import SQLiteManager
from analytics.models import SystemMetrics


class AnalyticsManager:
    """
    Gestor de métricas y analíticas internas para OmniLocal-Core (Módulo 15).
    Consulta métricas agregadas del sistema (memorias, sesiones, interacciones, feedback score).
    Regla arquitectónica: NO escribe SQL directo. Utiliza únicamente SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.db_manager.create_tables()

    def get_system_metrics(self) -> SystemMetrics:
        """
        Calcula y devuelve una instancia de SystemMetrics con la información agregada:
        - total_memories: registros en la tabla memories
        - total_sessions: registros en la tabla context_sessions
        - total_interactions: memorias episódicas registradas
        - average_feedback_score: promedio de ratings en interaction_feedback (0.0 si no hay datos)
        """
        total_memories = self.db_manager.count_memories()
        total_sessions = self.db_manager.count_sessions()
        total_interactions = self.db_manager.count_interactions()
        avg_score = self.db_manager.average_feedback_score()

        return SystemMetrics(
            total_memories=total_memories,
            total_sessions=total_sessions,
            total_interactions=total_interactions,
            average_feedback_score=round(avg_score, 2) if isinstance(avg_score, float) else avg_score
        )
