from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_validation.manager import ExecutionValidationManager
from maintenance_validation.models import ExecutionValidationReport
from maintenance_approval.models import ExecutionApproval


class ExecutionApprovalManager:
    """Módulo 33: Capa de aprobación formal para planes de ejecución validados."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        validation_manager: Optional[ExecutionValidationManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.validation_manager = (
            validation_manager or ExecutionValidationManager(db_manager=self.db_manager)
        )

    def evaluate_approval(
        self,
        plan_id: Optional[int] = None,
        validation_id: Optional[int] = None,
        validation_report: Optional[ExecutionValidationReport] = None,
    ) -> ExecutionApproval:
        """Evalúa un reporte de validación y determina el estado formal de aprobación del plan."""
        target_report = validation_report

        if target_report is None and validation_id is not None:
            raw = self.db_manager.get_validation_report(validation_id)
            if raw:
                target_report = ExecutionValidationReport(
                    id=raw["id"],
                    plan_id=raw["plan_id"],
                    valid=raw["valid"],
                    risk_level=raw["risk_level"],
                    issues=raw["issues"],
                    recommendation=raw["recommendation"],
                    created_at=raw["created_at"],
                )

        if target_report is None:
            target_report = self.validation_manager.validate_plan(plan_id=plan_id)

        # Reglas de Aprobación Formal
        # 1. Validación correcta + riesgo bajo -> approved
        if target_report.valid and target_report.risk_level == "low":
            approval_status = "approved"
            approved = True
            reason = "Aprobación automática concedida: el plan fue validado correctamente con nivel de riesgo bajo."

        # 2. Validación correcta + riesgo medio -> requires_review
        elif target_report.valid and target_report.risk_level == "medium":
            approval_status = "requires_review"
            approved = False
            reason = "Aprobación en espera: el plan fue validado correctamente pero posee nivel de riesgo medio y requiere revisión manual."

        # 3. Validación inválida o riesgo alto -> rejected
        else:
            approval_status = "rejected"
            approved = False
            reason = "Aprobación rechazada: el plan es inválido o presenta riesgos no aceptables."

        p_id = target_report.plan_id
        val_id = target_report.id if target_report.id is not None else 0

        approval = ExecutionApproval(
            plan_id=p_id,
            validation_id=val_id,
            approval_status=approval_status,
            approved=approved,
            reason=reason,
        )

        approval_id = self.db_manager.insert_execution_approval(
            plan_id=approval.plan_id,
            validation_id=approval.validation_id,
            approval_status=approval.approval_status,
            approved=approval.approved,
            reason=approval.reason,
        )
        approval.id = approval_id

        return approval

    def get_execution_approval(self, approval_id: int) -> Optional[dict]:
        """Obtiene una aprobación por su ID."""
        return self.db_manager.get_execution_approval(approval_id)

    def get_execution_approvals(self) -> List[dict]:
        """Obtiene el historial de aprobaciones registradas."""
        return self.db_manager.get_execution_approvals()
