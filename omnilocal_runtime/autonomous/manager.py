from typing import Optional, Dict, Any, List
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.workflows.engine import WorkflowEngine
from omnilocal_runtime.bindings.manager import CapabilityBindingManager
from omnilocal_runtime.bindings.memory_binding import MemoryCapabilityBinding
from omnilocal_runtime.autonomous.models import AutonomousExecutionCycle


class AutonomousWorkflowManager:
    """
    Gestor de Ejecución Autónoma Completa de Workflows (Runtime Block 04).
    Ejecuta workflows autónomos completos mediante CapabilityBindingManager y genera ciclos trazables.
    """

    def __init__(
        self,
        workflow_engine: Optional[WorkflowEngine] = None,
        binding_manager: Optional[CapabilityBindingManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()

        if binding_manager:
            self.binding_manager = binding_manager
        else:
            self.binding_manager = CapabilityBindingManager(db_manager=self.db_manager)
            mem_binding = MemoryCapabilityBinding(db_manager=self.db_manager)
            mem_binding.register_all(self.binding_manager)

        if workflow_engine:
            self.workflow_engine = workflow_engine
            if not self.workflow_engine.capability_binding_manager:
                self.workflow_engine.capability_binding_manager = self.binding_manager
        else:
            engine = OmniLocalEngine(db_manager=self.db_manager)
            self.workflow_engine = WorkflowEngine(
                engine=engine,
                capability_binding_manager=self.binding_manager,
                db_manager=self.db_manager,
            )

    def start_cycle(self, workflow_id: str = "memory_optimization") -> AutonomousExecutionCycle:
        """Inicia un ciclo autónomo en estado 'running' y lo persiste en la base de datos."""
        cycle_id = self.db_manager.insert_autonomous_cycle(
            workflow_id=workflow_id,
            status="running",
            completed_stages=0,
            failed_stages=0,
            total_stages=9,
            success_rate=0.0,
        )
        return AutonomousExecutionCycle(
            id=cycle_id,
            workflow_id=workflow_id,
            status="running",
            completed_stages=0,
            failed_stages=0,
            total_stages=9,
            success_rate=0.0,
        )

    def execute_cycle(
        self,
        workflow_id: str = "memory_optimization",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AutonomousExecutionCycle:
        """
        Ejecuta un workflow completo autónomo utilizando capacidades reales mediante CapabilityBindingManager,
        registrando el progreso etapa a etapa y calculando el success_rate final y el estado del ciclo.
        """
        cycle = self.start_cycle(workflow_id)

        meta = metadata or {}
        meta["autonomous_cycle_id"] = cycle.id

        execution = self.workflow_engine.execute_workflow(workflow_id, metadata=meta)

        results = execution.results or []
        completed_stages = 0
        failed_stages = 0

        for r in results:
            if r.get("status") == "completed" or r.get("success") is True:
                completed_stages += 1
            else:
                failed_stages += 1

        total_stages = len(results) if len(results) > 0 else 9
        success_rate = (completed_stages / total_stages) * 100.0 if total_stages > 0 else 0.0

        if failed_stages == 0 and completed_stages == total_stages:
            status = "completed"
        elif completed_stages > 0 and failed_stages > 0:
            status = "partial"
        elif completed_stages == 0 and failed_stages > 0:
            status = "failed"
        else:
            status = "completed"

        cycle.completed_stages = completed_stages
        cycle.failed_stages = failed_stages
        cycle.total_stages = total_stages
        cycle.success_rate = success_rate
        cycle.status = status
        cycle.details = results

        self.db_manager.update_autonomous_cycle(
            cycle_id=cycle.id,
            status=status,
            completed_stages=completed_stages,
            failed_stages=failed_stages,
            total_stages=total_stages,
            success_rate=success_rate,
        )

        return cycle

    def get_cycle(self, cycle_id: int) -> Optional[AutonomousExecutionCycle]:
        """Obtiene un ciclo de ejecución autónoma por ID."""
        row = self.db_manager.get_autonomous_cycle(cycle_id)
        if not row:
            return None
        return AutonomousExecutionCycle(
            id=row["id"],
            workflow_id=row["workflow_id"],
            status=row["status"],
            completed_stages=row["completed_stages"],
            failed_stages=row["failed_stages"],
            total_stages=row["total_stages"],
            success_rate=row["success_rate"],
            created_at=row.get("created_at"),
        )

    def get_cycles(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de todos los ciclos de ejecución autónoma registrados."""
        return self.db_manager.get_autonomous_cycles()
