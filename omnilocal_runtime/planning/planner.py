from typing import List, Dict, Any, Union, Optional
import json
from omnilocal_runtime.planning.models import RuntimeExecutionPlan, RuntimePlanStep
from omnilocal_runtime.planning.risk import RuntimeRiskEvaluator


class RuntimePlannerEngine:
    """
    Motor de Planificación Autónomo (Runtime Block 11).
    Transforma un KnowledgeAwareDecisionReport en un RuntimeExecutionPlan estructurado
    de pasos ordenados y estimación de riesgo.
    """

    @staticmethod
    def _extract_field(obj: Union[Dict[str, Any], Any], field: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)

    @staticmethod
    def generate_steps(
        decision_type: str,
        reasoning: str = "",
        knowledge_entries: Optional[List[Any]] = None
    ) -> List[RuntimePlanStep]:
        """
        Genera una lista de pasos ordenados (RuntimePlanStep) en función del tipo de decisión.
        """
        decision_type = str(decision_type).lower()
        steps: List[RuntimePlanStep] = []

        if decision_type == "fallback":
            steps = [
                RuntimePlanStep(
                    step_number=1,
                    action="verify_contingency_triggers",
                    description="Verificar condiciones de disparo de contingencia y estado de degradación",
                    expected_result="Confirmación de necesidad de fallback seguro",
                    risk_level="high"
                ),
                RuntimePlanStep(
                    step_number=2,
                    action="isolate_faulty_pipeline",
                    description="Aislar módulo o componente comprometido para prevenir propagación de fallos",
                    expected_result="Componente inestable enrutado a canal de aislamiento",
                    risk_level="medium"
                ),
                RuntimePlanStep(
                    step_number=3,
                    action="prepare_safe_mode_proposal",
                    description="Generar propuesta de configuración en modo seguro de respaldo",
                    expected_result="Propuesta de fallback lista para aprobación",
                    risk_level="low"
                )
            ]
        elif decision_type == "investigate":
            steps = [
                RuntimePlanStep(
                    step_number=1,
                    action="inspect_telemetry_logs",
                    description="Inspeccionar logs de observabilidad, trazas de error y latencia pico",
                    expected_result="Diagnóstico inicial de cuellos de botella e inestabilidad",
                    risk_level="low"
                ),
                RuntimePlanStep(
                    step_number=2,
                    action="isolate_anomaly_patterns",
                    description="Mapear patrones anómalos contra base de conocimiento histórico",
                    expected_result="Identificación de causas raíz probables",
                    risk_level="medium"
                ),
                RuntimePlanStep(
                    step_number=3,
                    action="formulate_diagnostic_report",
                    description="Redactar propuesta de investigación detallada para el operador",
                    expected_result="Informe de diagnóstico generado",
                    risk_level="low"
                )
            ]
        elif decision_type == "optimize":
            steps = [
                RuntimePlanStep(
                    step_number=1,
                    action="analyze_validation_stage",
                    description="Analizar métricas de validación y rendimiento en la etapa actual",
                    expected_result="Oportunidades de optimización identificadas",
                    risk_level="low"
                ),
                RuntimePlanStep(
                    step_number=2,
                    action="review_failure_pattern",
                    description="Revisar patrones de fallo pasados y candidatos a caché/paralelización",
                    expected_result="Estrategia de caché y ajuste parametrizada",
                    risk_level="low"
                ),
                RuntimePlanStep(
                    step_number=3,
                    action="generate_optimization_proposal",
                    description="Generar propuesta de optimización de latencia y uso de recursos",
                    expected_result="Plan de optimización estructurado",
                    risk_level="low"
                )
            ]
        else:  # "continue" or general
            steps = [
                RuntimePlanStep(
                    step_number=1,
                    action="audit_pipeline_stability",
                    description="Auditar estabilidad general de la canalización de ejecución",
                    expected_result="Verificación de estado operativo óptimo",
                    risk_level="low"
                ),
                RuntimePlanStep(
                    step_number=2,
                    action="prepare_state_checkpoints",
                    description="Preparar puntos de control de estado para el siguiente ciclo",
                    expected_result="Checkpoints configurados",
                    risk_level="low"
                ),
                RuntimePlanStep(
                    step_number=3,
                    action="propose_continuation_flow",
                    description="Proponer flujo de continuación sin alteraciones de parámetros",
                    expected_result="Propuesta de continuación validada",
                    risk_level="low"
                )
            ]

        return steps

    @staticmethod
    def estimate_complexity(steps: List[RuntimePlanStep], decision_type: str) -> float:
        """
        Calcula una métrica de complejidad del plan basada en número de pasos y tipo de decisión.
        """
        base_complexity = len(steps) * 0.5
        d_type = str(decision_type).lower()
        if d_type == "fallback":
            base_complexity += 1.5
        elif d_type == "investigate":
            base_complexity += 1.0
        elif d_type == "optimize":
            base_complexity += 0.5

        return round(base_complexity, 2)

    @staticmethod
    def build_reasoning(decision_type: str, step_count: int, estimated_risk: str) -> str:
        """
        Construye la justificación textual del plan de ejecución autónomo.
        """
        return f"Plan de ejecución autónomo [{decision_type.upper()}_PLAN]: Consta de {step_count} pasos secuenciales con nivel de riesgo estimado [{estimated_risk.upper()}]. Propuesta preparada sin ejecución de acciones directas."

    @staticmethod
    def generate_plan(
        decision: Union[Dict[str, Any], Any],
        knowledge_entries: Optional[List[Any]] = None
    ) -> RuntimeExecutionPlan:
        """
        Transforma una decisión dada en un RuntimeExecutionPlan.
        """
        source_id = int(RuntimePlannerEngine._extract_field(decision, "id", 0) or 0)
        decision_type = str(RuntimePlannerEngine._extract_field(decision, "decision_type", "continue")).lower()
        confidence = float(RuntimePlannerEngine._extract_field(decision, "confidence", 0.9) or 0.9)
        decision_reasoning = str(RuntimePlannerEngine._extract_field(decision, "reasoning", ""))

        # Mapear decision_type a plan_type
        if decision_type == "fallback":
            plan_type = "fallback_plan"
        elif decision_type == "investigate":
            plan_type = "investigation_plan"
        elif decision_type == "optimize":
            plan_type = "optimization_plan"
        else:
            plan_type = "optimization_plan"

        steps = RuntimePlannerEngine.generate_steps(decision_type, decision_reasoning, knowledge_entries)
        complexity = RuntimePlannerEngine.estimate_complexity(steps, decision_type)

        estimated_risk = RuntimeRiskEvaluator.evaluate_plan_risk(
            steps=steps,
            complexity=complexity,
            failure_history_count=0,
            decision_confidence=confidence
        )

        steps_dicts = [s.to_dict() for s in steps]
        steps_json = json.dumps(steps_dicts)

        plan_reasoning = RuntimePlannerEngine.build_reasoning(decision_type, len(steps), estimated_risk)

        return RuntimeExecutionPlan(
            source_decision_id=source_id,
            plan_type=plan_type,
            steps=steps_json,
            estimated_risk=estimated_risk,
            confidence=confidence,
            reasoning=plan_reasoning
        )
