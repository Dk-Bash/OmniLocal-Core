import json
from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_adaptive_decision.manager import AdaptiveDecisionManager
from maintenance_workflow.models import MaintenanceWorkflow


class MaintenanceWorkflowManager:
    """Módulo 43: Capa de Orquestación de Flujos de Trabajo de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        adaptive_decision_manager: Optional[AdaptiveDecisionManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.adaptive_decision_manager = (
            adaptive_decision_manager or AdaptiveDecisionManager(db_manager=self.db_manager)
        )

    def create_workflow(
        self,
        decision_id: Optional[int] = None,
        decision_data: Optional[dict] = None,
    ) -> List[MaintenanceWorkflow]:
        """
        Crea la representación estructurada del flujo de pasos necesarios para las decisiones.
        NO ejecuta acciones de mantenimiento real ni modifica datos históricos.
        """
        decisions_to_process = []

        if decision_data is not None:
            decisions_to_process.append(decision_data)
        elif decision_id is not None:
            d = self.db_manager.get_adaptive_decision(decision_id)
            if d:
                decisions_to_process.append(d)
        else:
            decisions_to_process = self.db_manager.get_adaptive_decisions()
            if not decisions_to_process:
                dec_objs = self.adaptive_decision_manager.generate_decisions()
                decisions_to_process = [
                    self.db_manager.get_adaptive_decision(d.id) for d in dec_objs if d.id
                ]

        workflows: List[MaintenanceWorkflow] = []

        for dec in decisions_to_process:
            if not dec:
                continue
            d_id = dec["id"]
            d_type = dec.get("decision_type", "adaptive")

            if d_type == "adaptive":
                wf_type = "adaptive_workflow"
                steps = [
                    "decision_review",
                    "policy_check",
                    "coordination",
                    "execution_validation",
                ]
            elif d_type == "conservative":
                wf_type = "standard_workflow"
                steps = [
                    "decision_review",
                    "policy_check",
                    "manual_approval",
                    "coordination",
                    "execution_validation",
                ]
            else:
                wf_type = "fallback_workflow"
                steps = [
                    "decision_review",
                    "policy_check",
                    "fallback_deferral",
                ]

            steps_json = json.dumps(steps)
            w_id = self.db_manager.insert_workflow(
                decision_id=d_id,
                workflow_type=wf_type,
                steps=steps_json,
                current_step=0,
                status="pending",
            )

            workflows.append(
                MaintenanceWorkflow(
                    id=w_id,
                    decision_id=d_id,
                    workflow_type=wf_type,
                    steps=steps,
                    current_step=0,
                    status="pending",
                )
            )

        return workflows

    def advance_step(self, workflow_id: int) -> Optional[dict]:
        """Avanza el paso actual en el flujo de trabajo."""
        wf = self.db_manager.get_workflow(workflow_id)
        if not wf:
            return None

        steps = json.loads(wf["steps"]) if isinstance(wf["steps"], str) else wf["steps"]
        curr_step = wf["current_step"] + 1

        if curr_step >= len(steps):
            new_status = "completed"
            curr_step = len(steps)
        else:
            new_status = "in_progress"

        self.db_manager.update_workflow_step(workflow_id, curr_step, new_status)
        return self.db_manager.get_workflow(workflow_id)

    def get_workflow(self, workflow_id: int) -> Optional[dict]:
        """Obtiene un flujo de trabajo por ID."""
        return self.db_manager.get_workflow(workflow_id)

    def get_workflows(self) -> List[dict]:
        """Obtiene la lista de flujos de trabajo registrados."""
        return self.db_manager.get_workflows()
