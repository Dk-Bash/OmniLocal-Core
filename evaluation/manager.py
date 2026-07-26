from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from evaluation.models import InteractionFeedback


class EvaluationManager:
    """
    Gestor de evaluaciones y feedback para OmniLocal-Core (Módulo 14).
    Almacena y consulta evaluaciones asociadas a interacciones.
    Regla arquitectónica: NO escribe SQL directo. Utiliza únicamente SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.db_manager.create_tables()

    def add_feedback(
        self,
        interaction_id: int,
        rating: int,
        confidence: float,
        comment: str = ""
    ) -> int:
        """
        Registra una evaluación asociada a una interacción.
        Valida que rating esté entre 1 y 5, y confidence entre 0.0 y 1.0.
        Devuelve el feedback_id generado.
        """
        feedback_obj = InteractionFeedback(
            interaction_id=interaction_id,
            rating=rating,
            confidence=confidence,
            comment=comment
        )

        feedback_id = self.db_manager.insert_interaction_feedback(
            interaction_id=feedback_obj.interaction_id,
            rating=feedback_obj.rating,
            confidence=feedback_obj.confidence,
            comment=feedback_obj.comment
        )
        return feedback_id

    def get_feedback(self, feedback_id: int) -> Optional[InteractionFeedback]:
        """
        Consulta un registro de evaluación por su feedback_id.
        Devuelve una instancia de InteractionFeedback o None si no existe.
        """
        row = self.db_manager.get_interaction_feedback_by_id(feedback_id)
        if row is None:
            return None
        return InteractionFeedback(**row)

    def get_interaction_feedback(self, interaction_id: int) -> List[InteractionFeedback]:
        """
        Consulta y devuelve la lista de evaluaciones asociadas a una interacción específica.
        """
        rows = self.db_manager.get_interaction_feedback_by_interaction(interaction_id)
        return [InteractionFeedback(**row) for row in rows]
