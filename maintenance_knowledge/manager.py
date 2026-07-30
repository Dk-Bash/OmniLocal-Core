from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_feedback.manager import ExecutionFeedbackManager
from maintenance_knowledge.models import KnowledgeEntry


class MaintenanceKnowledgeManager:
    """Módulo 37: Capa de extracción de conocimiento de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        feedback_manager: Optional[ExecutionFeedbackManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.feedback_manager = (
            feedback_manager or ExecutionFeedbackManager(db_manager=self.db_manager)
        )

    def extract_knowledge(
        self,
        feedback_id: Optional[int] = None,
        feedback_data: Optional[dict] = None,
    ) -> KnowledgeEntry:
        """Extrae conocimiento estructurado desde un registro de retroalimentación de ejecución."""
        target_feedback = feedback_data

        if target_feedback is None and feedback_id is not None:
            target_feedback = self.db_manager.get_execution_feedback(feedback_id)

        if target_feedback is None:
            fb_obj = self.feedback_manager.generate_feedback()
            target_feedback = self.db_manager.get_execution_feedback(fb_obj.id)

        fb_id = target_feedback["id"] if target_feedback and "id" in target_feedback else 0
        fb_type = target_feedback.get("feedback_type", "neutral") if target_feedback else "neutral"

        # Reglas del Módulo 37:
        # Feedback positivo -> success_pattern, confidence = 0.9
        # Feedback neutral  -> improvement_hint, confidence = 0.5
        # Feedback negativo -> failure_pattern, confidence = 0.8
        if fb_type == "positive":
            knowledge_type = "success_pattern"
            confidence = 0.9
            description = "Patrón de éxito identificado: la ejecución cumplió satisfactoriamente con los objetivos esperados."
        elif fb_type == "negative":
            knowledge_type = "failure_pattern"
            confidence = 0.8
            description = "Patrón de fallo identificado: se registraron deficiencias durante la ejecución que requieren atención."
        else:
            knowledge_type = "improvement_hint"
            confidence = 0.5
            description = "Pista de mejora identificada: la ejecución fue neutra o parcial, propicia para refinamiento continuo."

        k_id = self.db_manager.insert_knowledge(
            source_feedback_id=fb_id,
            knowledge_type=knowledge_type,
            description=description,
            confidence=confidence,
        )

        return KnowledgeEntry(
            id=k_id,
            source_feedback_id=fb_id,
            knowledge_type=knowledge_type,
            description=description,
            confidence=confidence,
        )

    def get_knowledge(self, knowledge_id: int) -> Optional[dict]:
        """Obtiene un registro de conocimiento por ID."""
        return self.db_manager.get_knowledge(knowledge_id)

    def get_all_knowledge(self) -> List[dict]:
        """Obtiene todo el conocimiento extraído de mantenimiento."""
        return self.db_manager.get_all_knowledge()
