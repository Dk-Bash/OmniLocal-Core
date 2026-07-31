from typing import Dict, Any, List, Optional
from omnilocal_runtime.authorization.models import (
    RuntimeExecutionAuthorization,
    RuntimeAuthorizationCondition
)
from omnilocal_runtime.authorization.policy import RuntimeAuthorizationPolicy


class RuntimeAuthorizationEvaluator:
    """
    Evaluador central que procesa los reportes de validación y simulación
    para emitir una autorización de ejecución formal.
    """

    @classmethod
    def generate_conditions(
        cls,
        validation_report: Dict[str, Any],
        confidence_score: float = 0.85,
        extra_checks: Optional[List[Dict[str, Any]]] = None
    ) -> List[RuntimeAuthorizationCondition]:
        """
        Genera el conjunto de condiciones evaluadas aplicando la política de autorización.
        """
        return RuntimeAuthorizationPolicy.evaluate_policy(
            validation_report=validation_report,
            confidence_score=confidence_score,
            extra_checks=extra_checks
        )

    @classmethod
    def calculate_authorization_score(cls, conditions: List[RuntimeAuthorizationCondition]) -> float:
        """
        Calcula un puntaje ponderado de autorización entre 0.0 y 1.0 según el estado de las condiciones.
        """
        if not conditions:
            return 0.0

        total_weight = 0.0
        earned_weight = 0.0

        severity_weights = {
            "critical": 4.0,
            "high": 3.0,
            "medium": 2.0,
            "info": 1.0,
            "low": 1.0
        }

        for c in conditions:
            w = severity_weights.get(c.severity.lower(), 1.0)
            total_weight += w

            if c.condition_status == "passed":
                earned_weight += w
            elif c.condition_status == "warning":
                earned_weight += (w * 0.5)
            elif c.condition_status == "failed":
                earned_weight += 0.0

        return round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    @classmethod
    def generate_reasoning(
        cls,
        conditions: List[RuntimeAuthorizationCondition],
        status: str,
        level: str,
        score: float
    ) -> str:
        """
        Sintetiza la explicación técnica y lógica de la decisión de autorización.
        """
        passed_count = sum(1 for c in conditions if c.condition_status == "passed")
        warning_count = sum(1 for c in conditions if c.condition_status == "warning")
        failed_count = sum(1 for c in conditions if c.condition_status == "failed")

        lines = [
            f"Evaluación de Autorización de Ejecución (Score: {score:.2%}).",
            f"Resumen de Condiciones: {passed_count} Aprobadas, {warning_count} Advertencias, {failed_count} Fallidas.",
            f"Estado Resultante: [{status.upper()}] con Nivel de Confianza/Acceso: [{level.upper()}]."
        ]

        if failed_count > 0:
            failed_names = [f"'{c.condition_name}' ({c.description})" for c in conditions if c.condition_status == "failed"]
            lines.append(f"Motivos de Rechazo/Inhabilitación: {'; '.join(failed_names)}.")

        if warning_count > 0:
            warning_names = [f"'{c.condition_name}' ({c.description})" for c in conditions if c.condition_status == "warning"]
            lines.append(f"Condiciones a Monitorear: {'; '.join(warning_names)}.")

        if status == "authorized":
            lines.append("El plan cuenta con la máxima idoneidad para proceder hacia la capa de ejecución.")
        elif status == "authorized_with_conditions":
            lines.append("El plan se autoriza bajo condicionantes de supervisión y monitoreo continuo.")
        else:
            lines.append("El plan NO se encuentra autorizado para ejecución hasta subsanar las objeciones.")

        return " ".join(lines)

    @classmethod
    def evaluate_authorization(
        cls,
        validation_report: Dict[str, Any],
        plan_id: int = 0,
        validation_id: int = 0,
        confidence_score: float = 0.85,
        extra_checks: Optional[List[Dict[str, Any]]] = None
    ) -> RuntimeExecutionAuthorization:
        """
        Método principal para derivar la autorización final de ejecución a partir de la validación previa.
        """
        conditions = cls.generate_conditions(
            validation_report=validation_report,
            confidence_score=confidence_score,
            extra_checks=extra_checks
        )

        score = cls.calculate_authorization_score(conditions)

        has_failed = any(c.condition_status == "failed" for c in conditions)
        has_warning = any(c.condition_status == "warning" for c in conditions)

        approved_names = [c.condition_name for c in conditions if c.condition_status == "passed"]
        rejected_names = [c.condition_name for c in conditions if c.condition_status in ["failed", "warning"]]

        if has_failed:
            auth_status = "rejected"
            auth_level = "blocked" if any(c.severity == "critical" for c in conditions if c.condition_status == "failed") else "restricted"
        elif has_warning:
            auth_status = "authorized_with_conditions"
            auth_level = "restricted" if score < 0.70 else "normal"
        else:
            auth_status = "authorized"
            auth_level = "high_trust" if score >= 0.90 else "normal"

        reasoning = cls.generate_reasoning(conditions, auth_status, auth_level, score)

        return RuntimeExecutionAuthorization(
            plan_id=plan_id,
            validation_id=validation_id,
            authorization_status=auth_status,
            authorization_level=auth_level,
            approved_conditions=approved_names,
            rejected_conditions=rejected_names,
            reasoning=reasoning,
            conditions=conditions
        )
