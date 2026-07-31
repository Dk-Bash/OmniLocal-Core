from typing import List, Dict, Any, Union
import json
from omnilocal_runtime.planning.models import RuntimePlanStep


class RuntimeRiskEvaluator:
    """
    Evaluador de Riesgo para Planes Autónomos (Runtime Block 11).
    Evalúa la complejidad del plan, cantidad de pasos, historial de fallos y confianza de la decisión.
    """

    @staticmethod
    def calculate_risk_score(
        step_count: int,
        complexity: float,
        failure_history_count: int = 0,
        decision_confidence: float = 0.9
    ) -> float:
        """
        Calcula una puntuación de riesgo numérica entre 0.0 (mínimo) y 1.0 (crítico).
        """
        # A mayor número de pasos y complejidad, mayor riesgo
        base_risk = (step_count * 0.08) + (complexity * 0.15)
        # Historial de fallos incrementa el riesgo
        history_penalty = min(failure_history_count * 0.05, 0.25)
        # Menor confianza en la decisión incrementa el riesgo
        confidence_risk = (1.0 - max(0.1, min(decision_confidence, 1.0))) * 0.3

        total_score = base_risk + history_penalty + confidence_risk
        return round(min(max(total_score, 0.05), 0.99), 2)

    @staticmethod
    def evaluate_plan_risk(
        steps: List[Union[RuntimePlanStep, Dict[str, Any]]],
        complexity: float = 1.0,
        failure_history_count: int = 0,
        decision_confidence: float = 0.9
    ) -> str:
        """
        Mapea el risk score a un nivel cualitativo: low, medium, high, critical.
        """
        step_count = len(steps)
        # Comprobar si algún paso tiene risk_level crítico o alto explícito
        has_critical_step = any(
            (s.get("risk_level") if isinstance(s, dict) else getattr(s, "risk_level", "low")) == "critical"
            for s in steps
        )
        has_high_step = any(
            (s.get("risk_level") if isinstance(s, dict) else getattr(s, "risk_level", "low")) == "high"
            for s in steps
        )

        score = RuntimeRiskEvaluator.calculate_risk_score(
            step_count=step_count,
            complexity=complexity,
            failure_history_count=failure_history_count,
            decision_confidence=decision_confidence
        )

        if has_critical_step or score >= 0.75:
            return "critical"
        elif has_high_step or score >= 0.50:
            return "high"
        elif score >= 0.25:
            return "medium"
        else:
            return "low"

    @staticmethod
    def generate_risk_summary(risk_level: str, risk_score: float, step_count: int) -> str:
        """
        Genera un resumen textual explicativo sobre el nivel de riesgo asignado.
        """
        return f"Evaluación de Riesgo [{risk_level.upper()}] (score: {risk_score}): Basado en {step_count} pasos estructurados de propuesta de ejecución."
