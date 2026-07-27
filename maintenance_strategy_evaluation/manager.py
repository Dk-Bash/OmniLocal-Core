from datetime import datetime
from typing import Optional, List
from maintenance_strategy.manager import MaintenanceStrategyManager
from database.sqlite_manager import SQLiteManager
from .models import StrategyEvaluation


class StrategyEvaluationManager:
    """
    Capa de Evaluación de Estrategia de Mantenimiento para OmniLocal-Core (Módulo 27).
    Evalúa la calidad, impacto y confianza de una estrategia propuesta.
    NO ejecuta mantenimiento, NO modifica memorias, NO altera auditorías.
    Todo SQL permanece únicamente dentro de SQLiteManager.
    """

    def __init__(
        self,
        strategy_manager: Optional[MaintenanceStrategyManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        self.strategy_manager = strategy_manager or MaintenanceStrategyManager()
        self.db_manager = db_manager or SQLiteManager()

    def evaluate_strategy(self, strategy_id: str) -> StrategyEvaluation:
        """
        Obtiene la estrategia usando MaintenanceStrategyManager,
        evalúa sus características y guarda una StrategyEvaluation en SQLite.
        """
        recommendations = self.strategy_manager.generate_strategy()

        recommended_priority = "deferred"
        matched_rec = None

        # Intentar asociar strategy_id con recomendaciones existentes
        for rec in recommendations:
            if (
                str(rec.id) == str(strategy_id)
                or rec.task_type == str(strategy_id)
                or rec.recommended_priority == str(strategy_id)
            ):
                matched_rec = rec
                break

        if matched_rec:
            recommended_priority = matched_rec.recommended_priority
        else:
            s_lower = str(strategy_id).lower()
            if "immediate" in s_lower:
                recommended_priority = "immediate"
            elif "soon" in s_lower:
                recommended_priority = "soon"
            elif "planned" in s_lower:
                recommended_priority = "planned"
            elif "deferred" in s_lower:
                recommended_priority = "deferred"

        if recommended_priority == "immediate":
            quality_score = 1.0
            impact_score = 1.0
            confidence_score = 0.9
            summary = "Strategy showed maximum expected improvement and immediate execution quality."
        elif recommended_priority == "soon":
            quality_score = 0.8
            impact_score = 0.8
            confidence_score = 0.8
            summary = "Strategy showed high expected improvement and short-term value."
        elif recommended_priority == "planned":
            quality_score = 0.6
            impact_score = 0.6
            confidence_score = 0.7
            summary = "Strategy showed moderate expected improvement for routine planning."
        else:
            quality_score = 0.3
            impact_score = 0.3
            confidence_score = 0.5
            summary = "Strategy showed low expected priority and deferred execution impact."

        eval_obj = StrategyEvaluation(
            strategy_id=str(strategy_id),
            quality_score=quality_score,
            impact_score=impact_score,
            confidence_score=confidence_score,
            summary=summary,
            created_at=datetime.now(),
        )

        # Guardar evaluación utilizando SQLiteManager
        eval_id = self.db_manager.insert_strategy_evaluation(
            strategy_id=eval_obj.strategy_id,
            quality_score=eval_obj.quality_score,
            impact_score=eval_obj.impact_score,
            confidence_score=eval_obj.confidence_score,
            summary=eval_obj.summary,
            created_at=eval_obj.created_at.isoformat(),
        )
        eval_obj.id = eval_id

        return eval_obj

    def get_evaluations(self) -> List[StrategyEvaluation]:
        """Recupera todas las evaluaciones estratégicas almacenadas."""
        raw_evals = self.db_manager.get_strategy_evaluations()
        result = []
        for r in raw_evals:
            created_dt = (
                datetime.fromisoformat(r["created_at"])
                if isinstance(r["created_at"], str)
                else r["created_at"]
            )
            result.append(
                StrategyEvaluation(
                    id=r["id"],
                    strategy_id=r["strategy_id"],
                    quality_score=r["quality_score"],
                    impact_score=r["impact_score"],
                    confidence_score=r["confidence_score"],
                    summary=r["summary"],
                    created_at=created_dt,
                )
            )
        return result
