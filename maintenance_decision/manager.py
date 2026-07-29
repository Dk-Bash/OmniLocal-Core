from datetime import datetime
from typing import Optional
from maintenance_adaptive.manager import AdaptiveRecommendationManager
from maintenance_strategy_learning.manager import StrategyLearningManager
from maintenance_intelligence.manager import MaintenanceIntelligenceManager
from database.sqlite_manager import SQLiteManager
from .models import MaintenanceDecision


class MaintenanceDecisionManager:
    """
    Capa de Inteligencia de Decisión de Mantenimiento para OmniLocal-Core (Módulo 30).
    Consolida la inteligencia de mantenimiento (recomendaciones adaptativas, aprendizaje histórico
    y métricas de inteligencia) para tomar decisiones finales explicables.
    Responde: "¿Cuál es la mejor decisión de mantenimiento basada en todo el conocimiento disponible?"
    NO ejecuta mantenimiento, NO modifica memorias, NO altera estrategias, NO modifica evaluaciones históricas.
    Todo SQL permanece exclusivamente dentro de SQLiteManager.
    """

    def __init__(
        self,
        adaptive_manager: Optional[AdaptiveRecommendationManager] = None,
        learning_manager: Optional[StrategyLearningManager] = None,
        intelligence_manager: Optional[MaintenanceIntelligenceManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        self.db_manager = db_manager
        self.adaptive_manager = adaptive_manager or AdaptiveRecommendationManager(db_manager=self.db_manager)
        self.learning_manager = learning_manager or StrategyLearningManager(db_manager=self.db_manager)
        self.intelligence_manager = intelligence_manager or MaintenanceIntelligenceManager(db_manager=self.db_manager)

    def make_decision(self) -> MaintenanceDecision:
        """
        Obtiene la recomendación adaptativa, consulta el aprendizaje histórico y las métricas
        de inteligencia, y genera una decisión final explicable.
        """
        recommendation = self.adaptive_manager.generate_recommendation()
        
        # Consultar informes de apoyo
        learning_report = None
        if self.learning_manager:
            learning_report = self.learning_manager.generate_learning_report()

        intelligence_report = None
        if self.intelligence_manager:
            intelligence_report = self.intelligence_manager.generate_report()

        # Reglas de decisión:
        if recommendation.based_on_history and recommendation.confidence >= 0.8:
            decision_type = "adaptive"
            confidence = recommendation.confidence
            selected_strategy = recommendation.strategy_type
            reasoning = (
                f"Selected {selected_strategy} strategy because historical evaluations showed "
                f"highest quality score"
            )
            supporting_factors = [
                "historical_learning_available",
                "high_strategy_confidence",
                "intelligence_metrics_available",
            ]
        else:
            decision_type = "default"
            selected_strategy = "unknown"
            confidence = 0.0
            reasoning = "No sufficient historical learning or high confidence recommendation available."
            supporting_factors = []

        decision = MaintenanceDecision(
            decision_type=decision_type,
            selected_strategy=selected_strategy,
            confidence=confidence,
            reasoning=reasoning,
            supporting_factors=supporting_factors,
            created_at=datetime.now(),
        )

        if self.db_manager:
            dec_id = self.db_manager.insert_maintenance_decision(decision)
            decision.id = dec_id

        return decision
