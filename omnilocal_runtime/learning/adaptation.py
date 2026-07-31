from typing import Dict, Any, Optional
from omnilocal_runtime.learning.models import RuntimeLearningRecord, RuntimeAdaptationRecommendation


class RuntimeAdaptationEngine:
    """
    Motor de Adaptación del Runtime (Runtime Block 08).
    Genera recomendaciones de adaptación basadas en aprendizajes previos.
    IMPORTANTE: No aplica cambios automáticamente ni modifica la lógica del Runtime.
    """

    @staticmethod
    def calculate_learning_confidence(patterns_count: int, total_executions: int) -> float:
        """
        Calcula la confianza matemática del aprendizaje (entre 0.0 y 1.0) basada en la muestra.
        """
        if total_executions <= 0:
            return 0.50

        ratio = patterns_count / max(total_executions, 1)
        sample_factor = min(total_executions / 10.0, 1.0)

        confidence = 0.50 + (ratio * 0.30) + (sample_factor * 0.20)
        return min(round(confidence, 2), 0.99)

    @staticmethod
    def generate_adaptation(learning_record: RuntimeLearningRecord) -> RuntimeAdaptationRecommendation:
        """
        Transforma un RuntimeLearningRecord en una recomendación de adaptación accionable.
        """
        learning_type = learning_record.learning_type
        pattern = learning_record.pattern_detected
        confidence = learning_record.confidence

        if learning_type == "failure_pattern":
            target_area = pattern if pattern else "validation"
            recommended_change = f"Ajustar estrategia y reintentos en el área '{target_area}' para mitigar fallos reincidentes."
            priority = "high" if confidence >= 0.8 else "medium"
            reasoning = f"Patrón de fallo detectado con confianza {confidence}. Requiere fortalecimiento de validaciones."

        elif learning_type == "performance":
            target_area = "execution_pipeline"
            recommended_change = "Optimizar la asignación de memoria y tiempos de espera en el Pipeline de Ejecución."
            priority = "medium"
            reasoning = f"Métricas de rendimiento sugieren oportunidad de optimización con nivel de confianza {confidence}."

        elif learning_type == "optimization":
            target_area = "workflow_engine"
            recommended_change = "Activar caché de contextos intermedios para reducir latencia en workflows complejos."
            priority = "low"
            reasoning = "El Runtime es estable; se sugiere optimización proactiva de recursos."

        elif learning_type == "recovery":
            target_area = "capability_binding"
            recommended_change = "Configurar un mecanismo de fallback automático para binding de capacidades."
            priority = "critical" if confidence >= 0.85 else "high"
            reasoning = f"Sugerencia de recuperación ante fallos de binding con confianza {confidence}."

        else:
            target_area = "general_runtime"
            recommended_change = f"Revisar y ajustar la configuración general para el patrón '{pattern}'."
            priority = "low"
            reasoning = f"Registro de aprendizaje general con confianza {confidence}."

        return RuntimeAdaptationRecommendation(
            learning_id=learning_record.id or 0,
            target_area=target_area,
            recommended_change=recommended_change,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning
        )

    @staticmethod
    def evaluate_impact(recommendation: RuntimeAdaptationRecommendation) -> Dict[str, Any]:
        """
        Evalúa el impacto estimado de aplicar la recomendación propuesta.
        """
        priority_weights = {
            "critical": 0.9,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25
        }

        weight = priority_weights.get(recommendation.priority.lower(), 0.5)
        estimated_improvement_pct = round(weight * recommendation.confidence * 40.0, 1)

        return {
            "recommendation_id": recommendation.id,
            "target_area": recommendation.target_area,
            "priority": recommendation.priority,
            "estimated_success_rate_increase_pct": estimated_improvement_pct,
            "risk_level": "low" if recommendation.priority in ["low", "medium"] else "medium",
            "requires_manual_approval": True
        }
