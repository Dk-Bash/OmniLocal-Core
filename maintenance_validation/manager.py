from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_execution.models import MaintenanceExecutionPlan
from maintenance_validation.models import ExecutionValidationReport


class ExecutionValidationManager:
    """Módulo 32: Capa de validación previa para los planes de ejecución de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        execution_manager: Optional[MaintenanceExecutionManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.execution_manager = (
            execution_manager or MaintenanceExecutionManager(db_manager=self.db_manager)
        )

    def validate_plan(
        self,
        plan_id: Optional[int] = None,
        plan: Optional[MaintenanceExecutionPlan] = None,
    ) -> ExecutionValidationReport:
        """Valida un plan de ejecución y genera un reporte de validación explicable."""
        target_plan = plan

        if target_plan is None and plan_id is not None:
            raw = self.db_manager.get_execution_plan(plan_id)
            if raw:
                target_plan = MaintenanceExecutionPlan(
                    id=raw["id"],
                    decision_type=raw["decision_type"],
                    strategy_type=raw["strategy_type"],
                    execution_steps=raw["execution_steps"],
                    risk_level=raw["risk_level"],
                    estimated_duration=raw["estimated_duration"],
                    requires_approval=raw["requires_approval"],
                    reasoning=raw["reasoning"],
                    created_at=raw["created_at"],
                )

        if target_plan is None:
            target_plan = self.execution_manager.create_execution_plan()

        # Evaluación de Reglas de Validación
        # 1. Plan inválido: execution_steps vacío
        if not target_plan.execution_steps or len(target_plan.execution_steps) == 0:
            valid = False
            risk_level = "high"
            issues = ["missing_execution_steps"]
            recommendation = "Plan inválido: no contiene pasos de ejecución definidos."

        # 2. Plan adaptive: requiere aprobación manual
        elif target_plan.decision_type == "adaptive" or target_plan.requires_approval:
            valid = True
            risk_level = "medium"
            issues = ["manual_approval_required"]
            recommendation = "Plan adaptativo válido; requiere aprobación manual previa antes de proceder."

        # 3. Plan default: válido sin observaciones
        elif target_plan.decision_type == "default":
            valid = True
            risk_level = "low"
            issues = []
            recommendation = "Plan por defecto válido, bajo riesgo."

        # 4. Caso general por defecto
        else:
            valid = True
            risk_level = target_plan.risk_level or "low"
            issues = []
            recommendation = "Plan de ejecución verificado correctamente."

        p_id = target_plan.id if target_plan.id is not None else 0

        report = ExecutionValidationReport(
            plan_id=p_id,
            valid=valid,
            risk_level=risk_level,
            issues=issues,
            recommendation=recommendation,
        )

        report_id = self.db_manager.insert_validation_report(report)
        report.id = report_id

        return report

    def get_validation_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un reporte de validación por su ID."""
        return self.db_manager.get_validation_report(report_id)

    def get_validation_reports(self) -> List[dict]:
        """Obtiene el historial de reportes de validación."""
        return self.db_manager.get_validation_reports()
