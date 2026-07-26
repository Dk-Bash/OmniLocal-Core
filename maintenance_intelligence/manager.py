from datetime import datetime
from typing import Optional
from maintenance_evaluation.manager import OutcomeEvaluationManager
from .models import MaintenanceIntelligenceReport


class MaintenanceIntelligenceManager:
    """
    Capa de inteligencia analítica de mantenimiento (Módulo 25).
    Analiza el historial completo de resultados evaluados y genera métricas y tendencias.
    NO ejecuta acciones, NO modifica datos, NO elimina información.
    """

    def __init__(
        self,
        eval_manager: Optional[OutcomeEvaluationManager] = None,
    ):
        self.eval_manager = eval_manager or OutcomeEvaluationManager()
        self.db_manager = self.eval_manager.db_manager

    def generate_report(self) -> MaintenanceIntelligenceReport:
        """
        Obtiene evaluaciones existentes y calcula métricas y tendencias.
        Devuelve un MaintenanceIntelligenceReport con los resultados acumulados.
        """
        total = self.db_manager.count_outcome_events()
        by_type = self.db_manager.count_outcomes_by_type()
        avg_score = self.db_manager.average_outcome_score()

        completed = by_type.get("positive", 0)
        blocked = by_type.get("neutral", 0)
        failed = by_type.get("negative", 0)

        most_common: Optional[str] = None
        if total > 0 and by_type:
            max_count = -1
            for r_type, count in by_type.items():
                if count > max_count:
                    max_count = count
                    most_common = r_type

        return MaintenanceIntelligenceReport(
            total_events=total,
            completed_events=completed,
            blocked_events=blocked,
            failed_events=failed,
            average_score=avg_score,
            most_common_result=most_common,
            created_at=datetime.now(),
        )
