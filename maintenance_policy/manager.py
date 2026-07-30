from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_policy.models import MaintenancePolicyResult


class MaintenancePolicyManager:
    """Módulo 44: Capa de Aplicación de Políticas de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        workflow_manager: Optional[MaintenanceWorkflowManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.workflow_manager = (
            workflow_manager or MaintenanceWorkflowManager(db_manager=self.db_manager)
        )

    def evaluate_policy(
        self,
        workflow_id: Optional[int] = None,
        workflow_data: Optional[dict] = None,
    ) -> List[MaintenancePolicyResult]:
        """
        Evalúa si los flujos de trabajo cumplen las políticas de seguridad del sistema.
        NO ejecuta acciones de mantenimiento ni modifica datos históricos.
        """
        workflows_to_evaluate = []

        if workflow_data is not None:
            workflows_to_evaluate.append(workflow_data)
        elif workflow_id is not None:
            wf = self.db_manager.get_workflow(workflow_id)
            if wf:
                workflows_to_evaluate.append(wf)
        else:
            workflows_to_evaluate = self.db_manager.get_workflows()
            if not workflows_to_evaluate:
                wf_objs = self.workflow_manager.create_workflow()
                workflows_to_evaluate = [
                    self.db_manager.get_workflow(w.id) for w in wf_objs if w.id
                ]

        results: List[MaintenancePolicyResult] = []

        for wf in workflows_to_evaluate:
            if not wf:
                continue
            w_id = wf["id"]
            wf_type = wf.get("workflow_type", "adaptive_workflow")

            if wf_type == "adaptive_workflow":
                allowed = True
                risk_level = "medium"
                violations = ""
                reasoning = (
                    "Política Aprobada: El flujo adaptativo cuenta con nivel de confianza "
                    "suficiente. Se permite continuar bajo monitoreo estándar."
                )
            elif wf_type == "standard_workflow":
                allowed = True
                risk_level = "low"
                violations = ""
                reasoning = (
                    "Política Aprobada: El flujo estándar cumple plenamente con los criterios "
                    "conservadores de bajo riesgo."
                )
            else:  # fallback_workflow
                allowed = False
                risk_level = "high"
                violations = "Fallback de seguridad activado por baja confianza histórica"
                reasoning = (
                    "Política Bloqueada: El flujo fallback excede el umbral de riesgo "
                    "permitido para ejecución automática. Requiere revisión manual o diferimiento."
                )

            p_id = self.db_manager.insert_policy_result(
                workflow_id=w_id,
                allowed=allowed,
                risk_level=risk_level,
                violations=violations,
                reasoning=reasoning,
            )

            results.append(
                MaintenancePolicyResult(
                    id=p_id,
                    workflow_id=w_id,
                    allowed=allowed,
                    risk_level=risk_level,
                    violations=violations,
                    reasoning=reasoning,
                )
            )

        return results

    def get_policy_result(self, policy_id: int) -> Optional[dict]:
        """Obtiene un resultado de evaluación de política por ID."""
        return self.db_manager.get_policy_result(policy_id)

    def get_policy_results(self) -> List[dict]:
        """Obtiene la lista de resultados de políticas registradas."""
        return self.db_manager.get_policy_results()
