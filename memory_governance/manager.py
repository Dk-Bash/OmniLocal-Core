from typing import Optional, List
from memory_priority.manager import MemoryPriorityManager
from memory_governance.models import MaintenanceApproval


class GovernanceManager:
    """Capa de evaluación y gobernanza de mantenimiento de memoria para OmniLocal-Core (Módulo 21)."""

    def __init__(self, priority_manager: Optional[MemoryPriorityManager] = None):
        self.priority_manager = priority_manager or MemoryPriorityManager()

    def evaluate_tasks(self) -> List[MaintenanceApproval]:
        """Obtiene las tareas priorizadas y evalúa el riesgo y estado de aprobación de cada una."""
        report = self.priority_manager.prioritize()
        approvals: List[MaintenanceApproval] = []

        for task in report.tasks:
            p_level = task.priority_level

            if p_level == "critical":
                risk_level = "high"
                approval_status = "requires_review"
                reason = "Modificar o revisar memoria crítica requiere validación previa"
            elif p_level == "high":
                risk_level = "medium"
                approval_status = "requires_review"
                reason = "Modificar importancia requiere revisión intermedia"
            elif p_level == "medium":
                risk_level = "low"
                approval_status = "approved"
                reason = "Aprobado automáticamente para revisión de duplicados"
            else:  # low or unknown
                risk_level = "low"
                approval_status = "approved"
                reason = "Aprobado automáticamente por bajo riesgo"

            approvals.append(
                MaintenanceApproval(
                    id=task.id,
                    task_type=task.task_type,
                    risk_level=risk_level,
                    approval_status=approval_status,
                    reason=reason
                )
            )

        return approvals
