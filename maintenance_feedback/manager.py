from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_result.manager import ExecutionResultManager
from maintenance_result.models import ExecutionResult
from maintenance_feedback.models import ExecutionFeedback


class ExecutionFeedbackManager:
    """Módulo 36: Capa de retroalimentación de ejecución de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        result_manager: Optional[ExecutionResultManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.result_manager = (
            result_manager or ExecutionResultManager(db_manager=self.db_manager)
        )

    def generate_feedback(
        self,
        result_id: Optional[int] = None,
        result_data: Optional[dict] = None,
        result_obj: Optional[ExecutionResult] = None,
    ) -> ExecutionFeedback:
        """Genera retroalimentación formal y score de calidad basado en el resultado de ejecución."""
        target_result = result_data

        if target_result is None and result_obj is not None:
            target_result = {
                "id": result_obj.id,
                "tracking_id": result_obj.tracking_id,
                "result_status": result_obj.result_status,
                "impact": result_obj.impact,
                "summary": result_obj.summary,
            }

        if target_result is None and result_id is not None:
            target_result = self.db_manager.get_execution_result(result_id)

        if target_result is None:
            res = self.result_manager.evaluate_result()
            target_result = self.db_manager.get_execution_result(res.id)

        r_id = target_result["id"] if target_result and "id" in target_result else 0
        r_status = target_result.get("result_status", "partial") if target_result else "partial"

        # Reglas del Módulo 36:
        # success -> positive, score=0.9
        # partial -> neutral, score=0.5
        # failed -> negative, score=0.1
        if r_status == "success":
            feedback_type = "positive"
            quality_score = 0.9
            learning_notes = "Retroalimentación positiva: la ejecución cumplió satisfactoriamente los objetivos planeados."
        elif r_status == "partial":
            feedback_type = "neutral"
            quality_score = 0.5
            learning_notes = "Retroalimentación neutral: la ejecución fue parcial o no completó totalmente el flujo."
        else:
            feedback_type = "negative"
            quality_score = 0.1
            learning_notes = "Retroalimentación negativa: la ejecución falló y requiere ajuste en el aprendizaje de estrategias."

        fb_id = self.db_manager.insert_execution_feedback(
            result_id=r_id,
            feedback_type=feedback_type,
            quality_score=quality_score,
            learning_notes=learning_notes,
        )

        return ExecutionFeedback(
            id=fb_id,
            result_id=r_id,
            feedback_type=feedback_type,
            quality_score=quality_score,
            learning_notes=learning_notes,
        )

    def get_feedback(self, feedback_id: int) -> Optional[dict]:
        """Obtiene un registro de feedback por ID."""
        return self.db_manager.get_execution_feedback(feedback_id)

    def get_execution_feedback(self, feedback_id: int) -> Optional[dict]:
        """Alias para get_feedback."""
        return self.get_feedback(feedback_id)

    def get_feedbacks(self) -> List[dict]:
        """Obtiene el historial de retroalimentación de ejecución."""
        return self.db_manager.get_execution_feedbacks()

    def get_execution_feedbacks(self) -> List[dict]:
        """Alias para get_feedbacks."""
        return self.get_feedbacks()
