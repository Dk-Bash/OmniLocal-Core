from typing import Optional, List
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.models import PrioritizedTask, PriorityReport


class MemoryPriorityManager:
    """Capa de priorización de mantenimiento de memoria para OmniLocal-Core (Módulo 20)."""

    def __init__(self, planning_manager: Optional[MaintenancePlanningManager] = None):
        self.planning_manager = planning_manager or MaintenancePlanningManager()

    def prioritize(self) -> PriorityReport:
        """Obtiene el plan de mantenimiento y asigna puntajes y niveles de prioridad a cada tarea."""
        plan = self.planning_manager.create_plan()
        prioritized_tasks: List[PrioritizedTask] = []

        for task in plan.tasks:
            task_type = task.task_type

            if task_type == "empty_memory_review":
                score = 0.9
                level = "critical"
            elif task_type == "importance_fix":
                score = 0.85
                level = "high"
            elif task_type == "duplicate_review":
                score = 0.6
                level = "medium"
            else:
                score = 0.3
                level = "low"

            prioritized_tasks.append(
                PrioritizedTask(
                    id=task.id,
                    task_type=task.task_type,
                    description=task.description,
                    priority_score=score,
                    priority_level=level,
                    status=task.status
                )
            )

        total_tasks = len(prioritized_tasks)
        critical_tasks = sum(1 for t in prioritized_tasks if t.priority_level == "critical")
        high_tasks = sum(1 for t in prioritized_tasks if t.priority_level == "high")
        medium_tasks = sum(1 for t in prioritized_tasks if t.priority_level == "medium")
        low_tasks = sum(1 for t in prioritized_tasks if t.priority_level == "low")

        return PriorityReport(
            total_tasks=total_tasks,
            critical_tasks=critical_tasks,
            high_tasks=high_tasks,
            medium_tasks=medium_tasks,
            low_tasks=low_tasks,
            tasks=prioritized_tasks
        )
