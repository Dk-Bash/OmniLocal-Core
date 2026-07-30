from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_policy.manager import MaintenancePolicyManager
from maintenance_coordination.models import CoordinationResult


class MaintenanceCoordinatorManager:
    """Módulo 45: Capa de Coordinación Autónoma de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        workflow_manager: Optional[MaintenanceWorkflowManager] = None,
        policy_manager: Optional[MaintenancePolicyManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.workflow_manager = (
            workflow_manager or MaintenanceWorkflowManager(db_manager=self.db_manager)
        )
        self.policy_manager = (
            policy_manager or MaintenancePolicyManager(db_manager=self.db_manager, workflow_manager=self.workflow_manager)
        )

    def coordinate(
        self,
        workflow_id: Optional[int] = None,
        policy_id: Optional[int] = None,
    ) -> List[CoordinationResult]:
        """
        Coordina de forma autónoma el flujo de mantenimiento unificando workflows y políticas.
        NO ejecuta mantenimiento real directamente ni modifica memorias o decisiones históricas.
        """
        policies_to_coordinate = []

        if policy_id is not None:
            p = self.db_manager.get_policy_result(policy_id)
            if p:
                policies_to_coordinate.append(p)
        elif workflow_id is not None:
            policies = [
                p for p in self.db_manager.get_policy_results()
                if p["workflow_id"] == workflow_id
            ]
            if not policies:
                policies = [
                    self.db_manager.get_policy_result(p_obj.id)
                    for p_obj in self.policy_manager.evaluate_policy(workflow_id=workflow_id)
                    if p_obj.id
                ]
            policies_to_coordinate.extend(policies)
        else:
            policies_to_coordinate = self.db_manager.get_policy_results()
            if not policies_to_coordinate:
                pol_objs = self.policy_manager.evaluate_policy()
                policies_to_coordinate = [
                    self.db_manager.get_policy_result(p.id) for p in pol_objs if p.id
                ]

        results: List[CoordinationResult] = []

        for pol in policies_to_coordinate:
            if not pol:
                continue
            p_id = pol["id"]
            wf_id = pol["workflow_id"]
            allowed = pol["allowed"]
            risk_level = pol.get("risk_level", "low")

            if allowed:
                coordination_status = "ready"
                next_action = "Proceed to execution validation"
                summary = (
                    f"Coordinación Lista: Flujo #{wf_id} validado correctamente bajo nivel de riesgo "
                    f"'{risk_level}'. Preparado para validación y aprobación de ejecución."
                )
            else:
                coordination_status = "blocked"
                next_action = "Waiting for manual approval"
                summary = (
                    f"Coordinación Bloqueada: Flujo #{wf_id} marcado como alto riesgo. "
                    f"Se detiene la coordinación automática a la espera de autorización manual."
                )

            c_id = self.db_manager.insert_coordination_result(
                workflow_id=wf_id,
                policy_id=p_id,
                coordination_status=coordination_status,
                next_action=next_action,
                summary=summary,
            )

            results.append(
                CoordinationResult(
                    id=c_id,
                    workflow_id=wf_id,
                    policy_id=p_id,
                    coordination_status=coordination_status,
                    next_action=next_action,
                    summary=summary,
                )
            )

        return results

    def get_coordination_result(self, coordination_id: int) -> Optional[dict]:
        """Obtiene un resultado de coordinación por ID."""
        return self.db_manager.get_coordination_result(coordination_id)

    def get_coordination_history(self) -> List[dict]:
        """Obtiene todo el historial de coordinación autónoma."""
        return self.db_manager.get_coordination_history()
