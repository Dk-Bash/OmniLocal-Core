from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_governance.manager import MaintenanceGovernanceManager
from maintenance_compliance.models import ComplianceReport


class MaintenanceComplianceManager:
    """Módulo 50: Capa de Validación de Cumplimiento Normativo."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        governance_manager: Optional[MaintenanceGovernanceManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.governance_manager = (
            governance_manager or MaintenanceGovernanceManager(db_manager=self.db_manager)
        )

    def validate_compliance(
        self,
        governance_id: Optional[int] = None,
    ) -> List[ComplianceReport]:
        """
        Valida si los procesos evaluados por gobernanza cumplen con la normativa del sistema.
        Mantiene estrictamente observabilidad de solo lectura.
        """
        evaluations_to_process = []

        if governance_id is not None:
            gov = self.db_manager.get_governance_evaluation(governance_id)
            if gov:
                evaluations_to_process.append(gov)
        else:
            evaluations = self.db_manager.get_governance_evaluations()
            if not evaluations:
                # Si no hay evaluaciones guardadas, realizarlas vía governance_manager
                generated_evals = self.governance_manager.evaluate_governance()
                evaluations = [
                    self.db_manager.get_governance_evaluation(e.id) for e in generated_evals if e.id
                ]
            evaluations_to_process.extend(evaluations)

        reports: List[ComplianceReport] = []

        for gov in evaluations_to_process:
            if not gov:
                continue
            g_id = gov["id"]
            gov_status = gov.get("governance_status", "approved")

            if gov_status == "approved":
                compliant = True
                score = 1.0
                violations = "Ninguna violación detectada."
                recommendation = "Cumplimiento 100%: Proceder con ejecución autónoma según plan."
            elif gov_status == "review_required":
                compliant = False
                score = 0.5
                violations = "Observación de cumplimiento: Proceso sujeto a revisión intermedia de seguridad."
                recommendation = "Cumplimiento Parcial (50%): Resolver revisiones pendientes antes de autorizar."
            elif gov_status == "blocked":
                compliant = False
                score = 0.0
                violations = "Violación de política: Intento de ejecución en estado de bloqueo supervisado."
                recommendation = "Sin Cumplimiento (0%): Detener operación y realizar auditoría de seguridad."
            else:
                compliant = True
                score = 1.0
                violations = "Sin violaciones registradas."
                recommendation = "Mantener estándar."

            rep_id = self.db_manager.insert_compliance_report(
                governance_id=g_id,
                compliant=compliant,
                violations=violations,
                compliance_score=score,
                recommendation=recommendation,
            )

            reports.append(
                ComplianceReport(
                    id=rep_id,
                    governance_id=g_id,
                    compliant=compliant,
                    violations=violations,
                    compliance_score=score,
                    recommendation=recommendation,
                )
            )

        return reports

    def get_compliance_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un informe de cumplimiento por ID."""
        return self.db_manager.get_compliance_report(report_id)

    def get_compliance_reports(self) -> List[dict]:
        """Obtiene todos los informes de cumplimiento."""
        return self.db_manager.get_compliance_reports()
