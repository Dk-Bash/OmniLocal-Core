from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_correlation.manager import MaintenanceCorrelationManager
from maintenance_adaptive_decision.models import AdaptiveDecision


class AdaptiveDecisionManager:
    """Módulo 41: Capa de Decisión Adaptativa de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        correlation_manager: Optional[MaintenanceCorrelationManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.correlation_manager = correlation_manager or MaintenanceCorrelationManager(db_manager=self.db_manager)

    def generate_decisions(
        self,
        correlation_id: Optional[int] = None,
        correlation_data: Optional[dict] = None,
    ) -> List[AdaptiveDecision]:
        """
        Genera decisiones adaptativas basadas en correlaciones de inteligencia histórica.
        NO ejecuta acciones de mantenimiento real ni modifica datos existentes.
        """
        correlations_to_process = []

        if correlation_data is not None:
            correlations_to_process.append(correlation_data)
        elif correlation_id is not None:
            c = self.db_manager.get_correlation(correlation_id)
            if c:
                correlations_to_process.append(c)
        else:
            correlations_to_process = self.db_manager.get_correlations()
            if not correlations_to_process:
                corr_objs = self.correlation_manager.generate_correlations()
                correlations_to_process = [
                    self.db_manager.get_correlation(c.id) for c in corr_objs if c.id
                ]

        decisions: List[AdaptiveDecision] = []

        for corr in correlations_to_process:
            if not corr:
                continue
            c_id = corr["id"]
            strat = corr.get("strategy_type", "adaptive")
            conf = float(corr.get("confidence", 0.8))
            success_rate = float(corr.get("success_rate", 0.8))

            if conf >= 0.8:
                d_type = "adaptive"
                recommended_strat = strat
                reasoning = (
                    f"Decisión adaptativa basada en alta confianza ({conf:.2f}) y tasa de éxito "
                    f"estimada de {success_rate * 100:.1f}%. Se recomienda continuar con '{recommended_strat}'."
                )
            elif conf >= 0.5:
                d_type = "conservative"
                recommended_strat = "planned" if strat == "high_risk" else strat
                reasoning = (
                    f"Decisión conservadora por confianza moderada ({conf:.2f}). "
                    f"Se recomienda estrategia supervisada '{recommended_strat}'."
                )
            else:
                d_type = "fallback"
                recommended_strat = "deferred"
                reasoning = (
                    f"Decisión fallback por baja confianza ({conf:.2f}). "
                    "Se difiere la ejecución hasta obtener mayor evidencia histórica."
                )

            d_id = self.db_manager.insert_adaptive_decision(
                correlation_id=c_id,
                decision_type=d_type,
                recommended_strategy=recommended_strat,
                confidence=conf,
                reasoning=reasoning,
            )

            decisions.append(
                AdaptiveDecision(
                    id=d_id,
                    correlation_id=c_id,
                    decision_type=d_type,
                    recommended_strategy=recommended_strat,
                    confidence=conf,
                    reasoning=reasoning,
                )
            )

        return decisions

    def get_adaptive_decision(self, decision_id: int) -> Optional[dict]:
        """Obtiene una decisión adaptativa por ID."""
        return self.db_manager.get_adaptive_decision(decision_id)

    def get_adaptive_decisions(self) -> List[dict]:
        """Obtiene la lista de decisiones adaptativas registradas."""
        return self.db_manager.get_adaptive_decisions()
