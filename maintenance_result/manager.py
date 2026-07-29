from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_tracking.manager import ExecutionTrackingManager
from maintenance_result.models import ExecutionResult


class ExecutionResultManager:
    """Módulo 35: Capa de resultado de ejecución de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        tracking_manager: Optional[ExecutionTrackingManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.tracking_manager = (
            tracking_manager or ExecutionTrackingManager(db_manager=self.db_manager)
        )

    def evaluate_result(
        self,
        tracking_id: Optional[int] = None,
        tracking_data: Optional[dict] = None,
    ) -> ExecutionResult:
        """Evalúa el resultado de un seguimiento de ejecución según su estado."""
        target_tracking = tracking_data

        if target_tracking is None and tracking_id is not None:
            target_tracking = self.db_manager.get_execution_tracking(tracking_id)

        if target_tracking is None:
            # Crear un seguimiento por defecto si no se proporciona
            tracking_obj = self.tracking_manager.create_tracking()
            target_tracking = self.db_manager.get_execution_tracking(tracking_obj.id)

        t_id = target_tracking["id"] if target_tracking and "id" in target_tracking else 0
        t_status = target_tracking.get("status", "pending") if target_tracking else "pending"

        # Reglas del Módulo 35:
        # completed -> success, positive
        # failed -> failed, negative
        # running / pending / cancelled -> partial, neutral
        if t_status == "completed":
            result_status = "success"
            impact = "positive"
            summary = "Ejecución completada exitosamente con impacto positivo en el sistema."
        elif t_status == "failed":
            result_status = "failed"
            impact = "negative"
            summary = "Ejecución fallida con impacto negativo registrado para análisis."
        else:
            result_status = "partial"
            impact = "neutral"
            summary = f"Ejecución en estado '{t_status}' categorizada como parcial con impacto neutral."

        result_id = self.db_manager.insert_execution_result(
            tracking_id=t_id,
            result_status=result_status,
            impact=impact,
            summary=summary,
        )

        return ExecutionResult(
            id=result_id,
            tracking_id=t_id,
            result_status=result_status,
            impact=impact,
            summary=summary,
        )

    def get_result(self, result_id: int) -> Optional[dict]:
        """Obtiene un resultado de ejecución por ID."""
        return self.db_manager.get_execution_result(result_id)

    def get_execution_result(self, result_id: int) -> Optional[dict]:
        """Alias para get_result."""
        return self.get_result(result_id)

    def get_results(self) -> List[dict]:
        """Obtiene el historial de resultados de ejecución."""
        return self.db_manager.get_execution_results()

    def get_execution_results(self) -> List[dict]:
        """Alias para get_results."""
        return self.get_results()
