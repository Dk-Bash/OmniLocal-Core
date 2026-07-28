from datetime import datetime
from typing import Optional
from maintenance_strategy_learning.manager import StrategyLearningManager
from maintenance_strategy.manager import MaintenanceStrategyManager
from database.sqlite_manager import SQLiteManager
from .models import AdaptiveRecommendation


class AdaptiveRecommendationManager:
    """
    Capa de Recomendación Adaptativa de Mantenimiento para OmniLocal-Core (Módulo 29).
    Recomienda estrategias futuras usando el aprendizaje histórico acumulado.
    Responde: "Basándose en experiencias anteriores, ¿qué estrategia conviene aplicar ahora?"
    NO ejecuta mantenimiento, NO modifica memorias, NO cambia estrategias existentes, NO altera evaluaciones.
    Todo SQL permanece exclusivamente dentro de SQLiteManager.
    """

    def __init__(
        self,
        learning_manager: Optional[StrategyLearningManager] = None,
        strategy_manager: Optional[MaintenanceStrategyManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        self.learning_manager = learning_manager or StrategyLearningManager()
        self.strategy_manager = strategy_manager or MaintenanceStrategyManager()
        self.db_manager = db_manager

    def generate_recommendation(self) -> AdaptiveRecommendation:
        """
        Obtiene el aprendizaje histórico y las estrategias disponibles, combina ambos resultados
        y genera una recomendación adaptativa.
        """
        learning_report = self.learning_manager.generate_learning_report()
        available_strategies = self.strategy_manager.generate_strategy()

        best_historical_type = learning_report.best_strategy_type

        if best_historical_type and learning_report.total_evaluations > 0 and best_historical_type != "unknown":
            strategy_type = best_historical_type
            confidence = 0.95
            based_on_history = True
            recommended_action = (
                f"Aplicar preferentemente la estrategia '{best_historical_type}' respaldada por "
                f"el aprendizaje de {learning_report.total_evaluations} evaluaciones previas."
            )
            reason = (
                f"Basándose en experiencias anteriores, la estrategia '{best_historical_type}' "
                f"ha demostrado la mayor efectividad histórica con una puntuación media de calidad "
                f"de {learning_report.average_quality_score:.2f}."
            )
        else:
            strategy_type = "unknown"
            confidence = 0.0
            based_on_history = False
            recommended_action = "No hay suficiente aprendizaje histórico para recomendar una estrategia adaptativa."
            reason = "No se encontraron evaluaciones estratégicas previas en el historial."

        recommendation = AdaptiveRecommendation(
            strategy_type=strategy_type,
            recommended_action=recommended_action,
            confidence=confidence,
            reason=reason,
            based_on_history=based_on_history,
            created_at=datetime.now(),
        )

        if self.db_manager:
            rec_id = self.db_manager.insert_adaptive_recommendation(recommendation)
            recommendation.id = rec_id

        return recommendation
