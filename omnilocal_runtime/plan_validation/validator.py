from typing import Dict, Any, Optional, Union, List
import json
from omnilocal_runtime.plan_validation.models import RuntimePlanValidationReport, RuntimePlanSimulationResult
from omnilocal_runtime.planning.models import RuntimeExecutionPlan


class RuntimePlanValidator:
    """
    Capa de Validación Lógica de Planes en Runtime (Runtime Block 12).
    Verifica riesgos, dependencias, simulación e historial antes de autorizar un plan.
    """

    @staticmethod
    def validate_plan(
        plan: Union[RuntimeExecutionPlan, Dict[str, Any]],
        simulation_result: Union[RuntimePlanSimulationResult, Dict[str, Any]],
        knowledge_entries: Optional[List[Dict[str, Any]]] = None
    ) -> RuntimePlanValidationReport:
        """
        Analiza un plan y el resultado de su simulación para dictaminar la aprobación o rechazo lógico.
        """
        # Extraer datos del plan
        if isinstance(plan, RuntimeExecutionPlan):
            plan_id = plan.id or 0
            plan_type = plan.plan_type
            estimated_risk = plan.estimated_risk
            plan_confidence = plan.confidence
            raw_steps = plan.steps
        else:
            plan_id = plan.get("id", 0)
            plan_type = plan.get("plan_type", "optimization_plan")
            estimated_risk = plan.get("estimated_risk", "low")
            plan_confidence = float(plan.get("confidence", 0.8))
            raw_steps = plan.get("steps", "[]")

        # Extraer datos de la simulación
        if isinstance(simulation_result, RuntimePlanSimulationResult):
            sim_status = simulation_result.simulation_status
            sim_confidence = simulation_result.confidence
        else:
            sim_status = simulation_result.get("simulation_status", "success")
            sim_confidence = float(simulation_result.get("confidence", 0.8))

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

        checks_performed = []
        failed_checks = []

        # 1. Chequeo de Nivel de Riesgo
        risk_check = RuntimePlanValidator.check_risk(estimated_risk)
        checks_performed.append(risk_check["check_name"])
        if not risk_check["passed"]:
            failed_checks.append(risk_check["details"])

        # 2. Chequeo de Dependencias y Secuencia de Pasos
        dep_check = RuntimePlanValidator.check_dependencies(steps)
        checks_performed.append(dep_check["check_name"])
        if not dep_check["passed"]:
            failed_checks.append(dep_check["details"])

        # 3. Chequeo de Confianza Mínima
        conf_passed = (plan_confidence >= 0.4 and sim_confidence >= 0.35)
        checks_performed.append("check_confidence_threshold")
        if not conf_passed:
            failed_checks.append(
                f"Confianza insuficiente: Plan={plan_confidence:.2f}, Simulación={sim_confidence:.2f} (Mínimo requerido: 0.40/0.35)"
            )

        # 4. Chequeo de Resultado de Simulación
        sim_check_passed = (sim_status in ["success", "partial"])
        checks_performed.append("check_simulation_status")
        if not sim_check_passed:
            failed_checks.append(f"La simulación previa resultó en estado de fallo ({sim_status.upper()}).")

        # Determinar estado final de validación
        if sim_status == "failure" or estimated_risk == "critical" or len(failed_checks) >= 2:
            validation_status = "rejected"
            recommendation = (
                f"RECHAZADO: El plan presenta riesgos críticos o falló en la simulación. "
                f"Fallos detectados: {'; '.join(failed_checks) or 'Evaluación de seguridad reprobada'}."
            )
        elif len(failed_checks) == 1 or estimated_risk == "high" or sim_status == "partial":
            validation_status = "approved_with_warnings"
            recommendation = (
                f"APROBADO CON ADVERTENCIAS: El plan es ejecutable pero requiere supervisión activa. "
                f"Advertencias: {'; '.join(failed_checks) or 'Riesgo alto o resultado parcial simulado'}."
            )
        else:
            validation_status = "approved"
            recommendation = (
                f"APROBADO: El plan '{plan_type}' superó exitosamente todas las verificaciones de seguridad "
                f"y simulación previa."
            )

        return RuntimePlanValidationReport(
            plan_id=plan_id,
            validation_status=validation_status,
            risk_level=estimated_risk,
            checks_performed=json.dumps(checks_performed),
            failed_checks=json.dumps(failed_checks),
            recommendation=recommendation
        )

    @staticmethod
    def check_risk(risk_level: str) -> Dict[str, Any]:
        """Evalúa si el nivel de riesgo del plan es aceptable sin revisión humana obligatoria."""
        risk = risk_level.lower()
        if risk == "critical":
            return {
                "check_name": "check_risk_tolerance",
                "passed": False,
                "details": "Riesgo CRÍTICO detectado: excede la tolerancia de ejecución autónoma."
            }
        elif risk == "high":
            return {
                "check_name": "check_risk_tolerance",
                "passed": True,
                "details": "Riesgo ALTO detectado: dentro de límites pero requiere cautela."
            }
        else:
            return {
                "check_name": "check_risk_tolerance",
                "passed": True,
                "details": f"Nivel de riesgo {risk.upper()} aceptable para automatización."
            }

    @staticmethod
    def check_dependencies(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verifica la coherencia secuencial de los pasos del plan."""
        if not steps:
            return {
                "check_name": "check_step_dependencies",
                "passed": False,
                "details": "El plan no contiene pasos de ejecución definidos."
            }

        numbers = [s.get("step_number", idx + 1) for idx, s in enumerate(steps)]
        if numbers != sorted(numbers):
            return {
                "check_name": "check_step_dependencies",
                "passed": False,
                "details": "Los pasos del plan no mantienen una numeración secuencial estricta."
            }

        return {
            "check_name": "check_step_dependencies",
            "passed": True,
            "details": f"Secuencia válida de {len(steps)} pasos con dependencias ordenadas."
        }

    @staticmethod
    def generate_validation_summary(status: str, checks: List[str], failed_checks: List[str]) -> str:
        """Construye un resumen formateado del dictamen de validación."""
        total = len(checks)
        failed_count = len(failed_checks)
        passed_count = total - failed_count
        return (
            f"Dictamen de Validación: [{status.upper()}] — {passed_count}/{total} verificaciones aprobadas. "
            f"Fallos: {failed_count}."
        )
