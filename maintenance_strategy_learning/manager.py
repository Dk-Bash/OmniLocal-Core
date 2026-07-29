from datetime import datetime
from typing import Optional
from database.sqlite_manager import SQLiteManager
from maintenance_strategy_evaluation.manager import StrategyEvaluationManager
from .models import StrategyLearningReport


class StrategyLearningManager:
    """
    Capa de Aprendizaje de Estrategias de Mantenimiento para OmniLocal-Core (Módulo 28).
    Analiza el historial de evaluaciones estratégicas para responder qué estrategias
    han demostrado mejores resultados anteriormente.
    NO ejecuta mantenimiento, NO modifica estrategias, NO cambia evaluaciones, NO elimina información.
    Todo SQL permanece únicamente dentro de SQLiteManager.
    """

    def __init__(
        self,
        evaluation_manager: Optional[StrategyEvaluationManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        if evaluation_manager:
            self.evaluation_manager = evaluation_manager
        elif db_manager:
            self.evaluation_manager = StrategyEvaluationManager(db_manager=db_manager)
        else:
            self.evaluation_manager = StrategyEvaluationManager()

    def generate_learning_report(self) -> StrategyLearningReport:
        """
        Obtiene evaluaciones históricas usando StrategyEvaluationManager y calcula
        métricas agregadas de calidad, impacto, confianza y identifica la mejor estrategia.
        """
        evaluations = self.evaluation_manager.get_evaluations()

        if not evaluations:
            return StrategyLearningReport(
                total_evaluations=0,
                average_quality_score=0.0,
                average_impact_score=0.0,
                average_confidence_score=0.0,
                best_strategy_type=None,
                learning_summary="No historical strategy evaluations available for learning analysis.",
                created_at=datetime.now(),
            )

        total_evaluations = len(evaluations)
        total_q = sum(e.quality_score for e in evaluations)
        total_i = sum(e.impact_score for e in evaluations)
        total_c = sum(e.confidence_score for e in evaluations)

        avg_q = round(total_q / total_evaluations, 4)
        avg_i = round(total_i / total_evaluations, 4)
        avg_c = round(total_c / total_evaluations, 4)

        # Identificar la evaluación con mayor quality_score
        sorted_evals = sorted(
            evaluations,
            key=lambda x: (x.quality_score, x.id if x.id is not None else 0),
            reverse=True,
        )
        best_eval = sorted_evals[0]

        s_id = str(best_eval.strategy_id).lower()
        if "immediate" in s_id:
            best_type = "immediate"
        elif "soon" in s_id:
            best_type = "soon"
        elif "planned" in s_id:
            best_type = "planned"
        elif "deferred" in s_id:
            best_type = "deferred"
        else:
            best_type = best_eval.strategy_id

        summary = (
            f"Analyzed {total_evaluations} historical strategy evaluation(s). "
            f"Average quality: {avg_q:.2f}, impact: {avg_i:.2f}, confidence: {avg_c:.2f}. "
            f"Highest performing strategy type: '{best_type}'."
        )

        return StrategyLearningReport(
            total_evaluations=total_evaluations,
            average_quality_score=avg_q,
            average_impact_score=avg_i,
            average_confidence_score=avg_c,
            best_strategy_type=best_type,
            learning_summary=summary,
            created_at=datetime.now(),
        )
