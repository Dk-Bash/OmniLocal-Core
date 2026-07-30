from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_adaptive_decision.manager import AdaptiveDecisionManager
from maintenance_optimization.models import OptimizationFeedback


class MaintenanceOptimizationManager:
    """Módulo 42: Capa de Bucle de Retroalimentación de Optimización de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        adaptive_decision_manager: Optional[AdaptiveDecisionManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.adaptive_decision_manager = (
            adaptive_decision_manager or AdaptiveDecisionManager(db_manager=self.db_manager)
        )

    def evaluate_optimization(
        self,
        decision_id: Optional[int] = None,
        decision_data: Optional[dict] = None,
        baseline_confidence: float = 0.70,
    ) -> List[OptimizationFeedback]:
        """
        Evalúa si las nuevas decisiones adaptativas mejoran el rendimiento
        respecto a niveles base previos o historiales registrados.
        NO ejecuta acciones de mantenimiento ni altera datos históricos.
        """
        decisions_to_evaluate = []

        if decision_data is not None:
            decisions_to_evaluate.append(decision_data)
        elif decision_id is not None:
            d = self.db_manager.get_adaptive_decision(decision_id)
            if d:
                decisions_to_evaluate.append(d)
        else:
            decisions_to_evaluate = self.db_manager.get_adaptive_decisions()
            if not decisions_to_evaluate:
                dec_objs = self.adaptive_decision_manager.generate_decisions()
                decisions_to_evaluate = [
                    self.db_manager.get_adaptive_decision(d.id) for d in dec_objs if d.id
                ]

        feedbacks: List[OptimizationFeedback] = []

        for dec in decisions_to_evaluate:
            if not dec:
                continue
            d_id = dec["id"]
            new_conf = float(dec.get("confidence", 0.8))
            prev_conf = baseline_confidence

            diff = round(new_conf - prev_conf, 4)

            if diff > 0.01:
                opt_type = "improved"
                summary = (
                    f"Optimización positiva: La confianza aumentó de {prev_conf:.2f} "
                    f"a {new_conf:.2f} (Ganancia: +{diff:.4f})."
                )
            elif diff < -0.01:
                opt_type = "degraded"
                summary = (
                    f"Desviación detectada: La confianza disminuyó de {prev_conf:.2f} "
                    f"a {new_conf:.2f} (Pérdida: {diff:.4f})."
                )
            else:
                opt_type = "stable"
                summary = (
                    f"Rendimiento estable: La confianza se mantiene en {new_conf:.2f} "
                    f"sin variaciones significativas."
                )

            f_id = self.db_manager.insert_optimization_feedback(
                decision_id=d_id,
                previous_confidence=prev_conf,
                new_confidence=new_conf,
                improvement_score=diff,
                optimization_type=opt_type,
                summary=summary,
            )

            feedbacks.append(
                OptimizationFeedback(
                    id=f_id,
                    decision_id=d_id,
                    previous_confidence=prev_conf,
                    new_confidence=new_conf,
                    improvement_score=diff,
                    optimization_type=opt_type,
                    summary=summary,
                )
            )

        return feedbacks

    def get_optimization_feedback(self, feedback_id: int) -> Optional[dict]:
        """Obtiene un registro de retroalimentación de optimización por ID."""
        return self.db_manager.get_optimization_feedback(feedback_id)

    def get_optimization_history(self) -> List[dict]:
        """Obtiene el historial completo de retroalimentación de optimización."""
        return self.db_manager.get_optimization_history()
