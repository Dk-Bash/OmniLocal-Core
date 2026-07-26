from typing import Optional, List
from memory_maintenance.manager import MaintenanceManager
from memory_planning.models import MaintenanceTask, MaintenancePlan


class MaintenancePlanningManager:
    """Capa de planificación de mantenimiento de memoria para OmniLocal-Core (Módulo 19)."""

    def __init__(self, maintenance_manager: Optional[MaintenanceManager] = None):
        self.maintenance_manager = maintenance_manager or MaintenanceManager()

    def create_plan(self) -> MaintenancePlan:
        """Obtiene recomendaciones de MaintenanceManager y las convierte en un MaintenancePlan organizado."""
        recommendations = self.maintenance_manager.generate_recommendations()
        tasks: List[MaintenanceTask] = []

        task_id = 1
        for rec in recommendations:
            issue_type = rec.issue_type

            if issue_type == "empty_content":
                tasks.append(
                    MaintenanceTask(
                        id=task_id,
                        task_type="empty_memory_review",
                        description=rec.recommendation or "Revisar memoria sin contenido",
                        priority="high",
                        status="pending"
                    )
                )
            elif issue_type == "duplicate_content":
                tasks.append(
                    MaintenanceTask(
                        id=task_id,
                        task_type="duplicate_review",
                        description=rec.recommendation or "Revisar memorias duplicadas",
                        priority="medium",
                        status="pending"
                    )
                )
            elif issue_type == "invalid_importance":
                tasks.append(
                    MaintenanceTask(
                        id=task_id,
                        task_type="importance_fix",
                        description=rec.recommendation or "Corregir nivel de importancia",
                        priority="high",
                        status="pending"
                    )
                )
            else:
                tasks.append(
                    MaintenanceTask(
                        id=task_id,
                        task_type=f"{issue_type}_review",
                        description=rec.recommendation or f"Revisar problema {issue_type}",
                        priority=rec.priority or "medium",
                        status="pending"
                    )
                )
            task_id += 1

        total_tasks = len(tasks)
        high_priority_tasks = sum(1 for t in tasks if t.priority == "high")
        medium_priority_tasks = sum(1 for t in tasks if t.priority == "medium")

        return MaintenancePlan(
            id=1,
            total_tasks=total_tasks,
            high_priority_tasks=high_priority_tasks,
            medium_priority_tasks=medium_priority_tasks,
            tasks=tasks
        )
