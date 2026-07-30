from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_patterns.manager import MaintenancePatternManager
from maintenance_improvement.models import ImprovementRecommendation


class MaintenanceImprovementManager:
    """Módulo 39: Capa de recomendaciones de mejora continua de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        pattern_manager: Optional[MaintenancePatternManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.pattern_manager = (
            pattern_manager or MaintenancePatternManager(db_manager=self.db_manager)
        )

    def generate_recommendations(
        self,
        pattern_id: Optional[int] = None,
        pattern_data: Optional[dict] = None,
    ) -> List[ImprovementRecommendation]:
        """Genera recomendaciones de mejora basadas en patrones detectados."""
        patterns_to_process = []

        if pattern_data is not None:
            patterns_to_process.append(pattern_data)
        elif pattern_id is not None:
            p = self.db_manager.get_pattern(pattern_id)
            if p:
                patterns_to_process.append(p)
        else:
            patterns_to_process = self.db_manager.get_patterns()
            if not patterns_to_process:
                detected_objs = self.pattern_manager.detect_patterns()
                patterns_to_process = [
                    self.db_manager.get_pattern(d.id) for d in detected_objs if d.id
                ]

        recommendations = []

        # Reglas Módulo 39:
        # frequent_failure -> recommendation_type = correction, priority = high
        # recurring_issue -> recommendation_type = prevention, priority = medium
        # frequent_success -> recommendation_type = optimization, priority = low
        for pat in patterns_to_process:
            if not pat:
                continue
            p_id = pat["id"]
            p_type = pat.get("pattern_type", "frequent_success")

            if p_type == "frequent_failure":
                rec_type = "correction"
                priority = "high"
                confidence = 0.9
                desc = "Recomendación de corrección: aplicar ajustes estructurales inmediatos para mitigar fallos frecuentes."
            elif p_type == "recurring_issue":
                rec_type = "prevention"
                priority = "medium"
                confidence = 0.75
                desc = "Recomendación de prevención: implementar controles preventivos frente a incidencias recurrentes."
            else:  # frequent_success
                rec_type = "optimization"
                priority = "low"
                confidence = 0.85
                desc = "Recomendación de optimización: estandarizar procedimientos y replicar los patrones exitosos."

            rec_id = self.db_manager.insert_improvement(
                pattern_id=p_id,
                recommendation_type=rec_type,
                priority=priority,
                description=desc,
                confidence=confidence,
            )

            recommendations.append(
                ImprovementRecommendation(
                    id=rec_id,
                    pattern_id=p_id,
                    recommendation_type=rec_type,
                    priority=priority,
                    description=desc,
                    confidence=confidence,
                )
            )

        return recommendations

    def get_improvement(self, improvement_id: int) -> Optional[dict]:
        """Obtiene una recomendación de mejora por ID."""
        return self.db_manager.get_improvement(improvement_id)

    def get_improvements(self) -> List[dict]:
        """Obtiene la lista de recomendaciones de mejora."""
        return self.db_manager.get_improvements()
