from typing import Dict, Any, List, Optional
from omnilocal_runtime.authorization.models import RuntimeAuthorizationCondition


class RuntimeAuthorizationPolicy:
    """
    Define y evalúa las políticas de autorización de ejecución para un plan validado.
    Garantiza que la toma de decisiones respete las reglas obligatorias de riesgo,
    confianza y estado de validación previo sin ejecutar ninguna acción real.
    """

    DEFAULT_MAX_ALLOWED_RISK = "high"  # "low", "medium", "high", "critical"
    MIN_CONFIDENCE_THRESHOLD = 0.50

    @classmethod
    def check_validation_status(cls, validation_report: Dict[str, Any]) -> RuntimeAuthorizationCondition:
        """
        Verifica el estado de la validación previa del plan.
        """
        val_status = validation_report.get("validation_status", "rejected")
        failed_checks = validation_report.get("failed_checks", [])

        if val_status == "approved":
            return RuntimeAuthorizationCondition(
                condition_name="validation_status_check",
                condition_status="passed",
                description="El plan ha superado exitosamente la capa de validación.",
                severity="info"
            )
        elif val_status == "approved_with_warnings":
            return RuntimeAuthorizationCondition(
                condition_name="validation_status_check",
                condition_status="warning",
                description=f"El plan fue aprobado con advertencias. Chequeos observados: {len(failed_checks)}.",
                severity="medium"
            )
        else:
            return RuntimeAuthorizationCondition(
                condition_name="validation_status_check",
                condition_status="failed",
                description="El plan fue rechazado en la capa de validación previa.",
                severity="critical"
            )

    @classmethod
    def check_risk_threshold(cls, risk_level: str) -> RuntimeAuthorizationCondition:
        """
        Verifica si el nivel de riesgo del plan está dentro de los umbrales aceptables.
        """
        normalized_risk = (risk_level or "medium").lower()

        if normalized_risk in ["low", "very_low"]:
            return RuntimeAuthorizationCondition(
                condition_name="risk_threshold_check",
                condition_status="passed",
                description=f"Nivel de riesgo ({normalized_risk}) dentro de límites óptimos.",
                severity="info"
            )
        elif normalized_risk == "medium":
            return RuntimeAuthorizationCondition(
                condition_name="risk_threshold_check",
                condition_status="passed",
                description="Nivel de riesgo moderado. Aceptable bajo supervisión estándar.",
                severity="info"
            )
        elif normalized_risk == "high":
            return RuntimeAuthorizationCondition(
                condition_name="risk_threshold_check",
                condition_status="warning",
                description="Nivel de riesgo alto. Requiere autorización condicionada.",
                severity="medium"
            )
        else:  # "critical", "extreme"
            return RuntimeAuthorizationCondition(
                condition_name="risk_threshold_check",
                condition_status="failed",
                description=f"Nivel de riesgo inaceptable ({normalized_risk}). Supera el umbral permitido.",
                severity="critical"
            )

    @classmethod
    def check_confidence_threshold(cls, confidence: float) -> RuntimeAuthorizationCondition:
        """
        Verifica si la confianza estimada supera el umbral mínimo exigido.
        """
        if confidence >= 0.75:
            return RuntimeAuthorizationCondition(
                condition_name="confidence_threshold_check",
                condition_status="passed",
                description=f"Nivel de confianza elevado ({confidence:.2%}).",
                severity="info"
            )
        elif confidence >= cls.MIN_CONFIDENCE_THRESHOLD:
            return RuntimeAuthorizationCondition(
                condition_name="confidence_threshold_check",
                condition_status="warning",
                description=f"Nivel de confianza aceptable ({confidence:.2%}), pero inferior al rango óptimo.",
                severity="medium"
            )
        else:
            return RuntimeAuthorizationCondition(
                condition_name="confidence_threshold_check",
                condition_status="failed",
                description=f"Confianza insuficiente ({confidence:.2%}). Menor al umbral de {cls.MIN_CONFIDENCE_THRESHOLD:.2%}.",
                severity="high"
            )

    @classmethod
    def check_mandatory_conditions(cls, validation_report: Dict[str, Any]) -> RuntimeAuthorizationCondition:
        """
        Verifica condiciones obligatorias de seguridad e integridad.
        """
        failed_checks = validation_report.get("failed_checks", [])
        critical_failures = [c for c in failed_checks if "critical" in str(c).lower() or "safety" in str(c).lower()]

        if not critical_failures:
            return RuntimeAuthorizationCondition(
                condition_name="mandatory_conditions_check",
                condition_status="passed",
                description="Todas las condiciones obligatorias de integridad han sido verificadas.",
                severity="info"
            )
        else:
            return RuntimeAuthorizationCondition(
                condition_name="mandatory_conditions_check",
                condition_status="failed",
                description=f"Se detectaron fallos críticos obligatorios: {', '.join(critical_failures)}.",
                severity="critical"
            )

    @classmethod
    def evaluate_policy(
        cls,
        validation_report: Dict[str, Any],
        confidence_score: float = 0.85,
        extra_checks: Optional[List[Dict[str, Any]]] = None
    ) -> List[RuntimeAuthorizationCondition]:
        """
        Ejecuta la evaluación completa de todas las reglas de la política.
        """
        conditions = []

        # 1. Validación previa
        conditions.append(cls.check_validation_status(validation_report))

        # 2. Umbral de Riesgo
        risk_level = validation_report.get("risk_level", "low")
        conditions.append(cls.check_risk_threshold(risk_level))

        # 3. Umbral de Confianza
        conditions.append(cls.check_confidence_threshold(confidence_score))

        # 4. Condiciones obligatorias
        conditions.append(cls.check_mandatory_conditions(validation_report))

        # 5. Chequeos adicionales opcionales
        if extra_checks:
            for chk in extra_checks:
                conditions.append(RuntimeAuthorizationCondition(
                    condition_name=chk.get("name", "custom_check"),
                    condition_status=chk.get("status", "passed"),
                    description=chk.get("description", "Chequeo personalizado"),
                    severity=chk.get("severity", "info")
                ))

        return conditions
