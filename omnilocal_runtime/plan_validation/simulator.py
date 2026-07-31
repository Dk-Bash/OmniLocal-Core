from typing import Dict, Any, Optional, Union, List
import json
from omnilocal_runtime.plan_validation.models import RuntimePlanSimulationResult
from omnilocal_runtime.planning.models import RuntimeExecutionPlan


class RuntimePlanSimulator:
    """
    Motor de Simulación Hipotética de Planes de Ejecución (Runtime Block 12).
    Evalúa qué pasaría si un plan se ejecutase en el futuro sin modificar ni disparar nada real.
    """

    @staticmethod
    def simulate_plan(
        plan: Union[RuntimeExecutionPlan, Dict[str, Any]],
        observability_metrics: Optional[Dict[str, Any]] = None
    ) -> RuntimePlanSimulationResult:
        """
        Simula la ejecución hipotética de un RuntimeExecutionPlan.
        Calcula el estado simulado, la predicción del resultado, posibles problemas y nivel de confianza.
        """
        # Extraer atributos del plan
        if isinstance(plan, RuntimeExecutionPlan):
            plan_id = plan.id or 0
            plan_type = plan.plan_type
            estimated_risk = plan.estimated_risk
            confidence = plan.confidence
            raw_steps = plan.steps
        else:
            plan_id = plan.get("id", 0)
            plan_type = plan.get("plan_type", "optimization_plan")
            estimated_risk = plan.get("estimated_risk", "low")
            confidence = float(plan.get("confidence", 0.8))
            raw_steps = plan.get("steps", "[]")

        # Parsear pasos
        if isinstance(raw_steps, str):
            try:
                steps = json.loads(raw_steps)
            except Exception:
                steps = []
        elif isinstance(raw_steps, list):
            steps = raw_steps
        else:
            steps = []

        step_count = len(steps)

        # Determinar estado de la simulación
        if estimated_risk == "critical" or confidence < 0.4:
            simulation_status = "failure"
        elif estimated_risk == "high" or confidence < 0.65:
            simulation_status = "partial"
        else:
            simulation_status = "success"

        # Calcular probabilidad de éxito ajustada
        sim_confidence = RuntimePlanSimulator.estimate_success_probability(
            plan_type=plan_type,
            step_count=step_count,
            risk_level=estimated_risk,
            plan_confidence=confidence
        )

        # Predecir resultado y problemas
        predicted_outcome = RuntimePlanSimulator.predict_outcome(plan_type, simulation_status, estimated_risk)
        predicted_issues = RuntimePlanSimulator._predict_issues(simulation_status, estimated_risk, step_count)

        return RuntimePlanSimulationResult(
            plan_id=plan_id,
            simulation_status=simulation_status,
            predicted_outcome=predicted_outcome,
            predicted_issues=predicted_issues,
            confidence=sim_confidence
        )

    @staticmethod
    def predict_outcome(plan_type: str, simulation_status: str, risk_level: str) -> str:
        """Genera la descripción del resultado proyectado del plan."""
        type_labels = {
            "optimization_plan": "Optimización de recursos y reducción de latencia",
            "recovery_plan": "Recuperación de la estabilidad del sistema",
            "investigation_plan": "Diagnóstico profundo y recolección de métricas",
            "fallback_plan": "Mitigación mediante modo degradado/fallback"
        }
        base_desc = type_labels.get(plan_type, "Ejecución de plan autónomo")

        if simulation_status == "success":
            return f"Simulación exitosa: {base_desc} proyectada de forma efectiva con riesgo {risk_level.upper()}."
        elif simulation_status == "partial":
            return f"Simulación parcial: {base_desc} alcanzará resultados moderados con posibles cuellos de botella."
        else:
            return f"Simulación fallida: {base_desc} presenta alto riesgo de interrupción o degradación de servicio."

    @staticmethod
    def estimate_success_probability(
        plan_type: str,
        step_count: int,
        risk_level: str,
        plan_confidence: float
    ) -> float:
        """Calcula la estimación probabilística de éxito de la simulación."""
        risk_penalties = {
            "low": 0.0,
            "medium": 0.08,
            "high": 0.22,
            "critical": 0.45
        }
        step_penalty = max(0, (step_count - 2) * 0.03)
        penalty = risk_penalties.get(risk_level.lower(), 0.1) + step_penalty

        prob = max(0.05, min(0.99, plan_confidence - penalty))
        return round(prob, 2)

    @staticmethod
    def generate_simulation_summary(
        plan_type: str,
        simulation_status: str,
        predicted_outcome: str,
        confidence: float
    ) -> str:
        """Construye un resumen legible de la simulación."""
        return (
            f"Resumen de Simulación ({plan_type}): Estado={simulation_status.upper()} | "
            f"Confianza={confidence:.2f} | Resultado: {predicted_outcome}"
        )

    @staticmethod
    def _predict_issues(simulation_status: str, risk_level: str, step_count: int) -> str:
        """Genera descripciones de posibles problemas predichos."""
        issues = []
        if risk_level in ["high", "critical"]:
            issues.append(f"Riesgo elevado ({risk_level.upper()}): requiere monitoreo estricto de recursos.")
        if step_count > 4:
            issues.append(f"Secuencia compleja ({step_count} pasos): posible desfase en tiempos de propagación.")
        if simulation_status == "failure":
            issues.append("Probable fallo por condiciones de entorno o métricas fuera de umbral de seguridad.")
        elif simulation_status == "partial":
            issues.append("Rendimiento subóptimo en pasos intermedios.")

        return " | ".join(issues) if issues else "Ningún problema mayor detectado durante la simulación."
