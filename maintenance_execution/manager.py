from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from maintenance_decision.manager import MaintenanceDecisionManager
from .models import MaintenanceExecutionPlan


class MaintenanceExecutionManager:
    """
    Gestor de Planificación de Ejecución de Mantenimiento (Módulo 31).
    Transforma decisiones inteligentes en planes de ejecución controlados.
    No ejecuta acciones reales, no modifica memorias, no cambia decisiones existentes ni estrategias.
    """

    def __init__(
        self,
        decision_manager: Optional[MaintenanceDecisionManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        if decision_manager:
            self.decision_manager = decision_manager
            self.db_manager = self.decision_manager.db_manager
        elif db_manager:
            self.db_manager = db_manager
            self.decision_manager = MaintenanceDecisionManager(db_manager=db_manager)
        else:
            self.decision_manager = MaintenanceDecisionManager()
            self.db_manager = self.decision_manager.db_manager

    def create_execution_plan(self) -> MaintenanceExecutionPlan:
        """
        Obtiene la decisión inteligente actual, la transforma en un plan de ejecución
        controlado con nivel de riesgo y duración estimada, y lo persiste en SQLite.
        """
        decision = self.decision_manager.make_decision()

        if decision.decision_type == "adaptive":
            risk_level = "medium"
            estimated_duration = "15m"
            requires_approval = True
            reasoning = "Plan adaptativo basado en historial y aprendizaje estratégico; requiere aprobación manual antes de ejecutar."
            steps = [
                "validate_strategy",
                "prepare_resources",
                "execute_controlled_maintenance",
                "record_result"
            ]
        else:
            risk_level = "low"
            estimated_duration = "0m"
            requires_approval = False
            reasoning = "Plan por defecto sin datos históricos suficientes; no requiere aprobación previa."
            steps = [
                "review_information",
                "wait_for_more_data"
            ]

        plan = MaintenanceExecutionPlan(
            decision_type=decision.decision_type,
            strategy_type=decision.selected_strategy,
            execution_steps=steps,
            risk_level=risk_level,
            estimated_duration=estimated_duration,
            requires_approval=requires_approval,
            reasoning=reasoning
        )

        plan_id = self.db_manager.insert_execution_plan(plan)
        plan.id = plan_id

        return plan

    def get_execution_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un plan de ejecución persistido por su ID."""
        return self.db_manager.get_execution_plan(plan_id)

    def get_execution_plans(self) -> List[Dict[str, Any]]:
        """Obtiene todos los planes de ejecución persistidos."""
        return self.db_manager.get_execution_plans()
