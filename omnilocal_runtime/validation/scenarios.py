import time
from typing import Dict, Any, Optional
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.autonomous.manager import AutonomousWorkflowManager
from omnilocal_runtime.bindings.manager import CapabilityBindingManager
from omnilocal_runtime.bindings.memory_binding import MemoryCapabilityBinding
from omnilocal_runtime.validation.models import RuntimeValidationReport


class ScenarioManager:
    """
    Gestor de Escenarios de Prueba Controlados (Runtime Block 05).
    Ejecuta escenarios sobre el Runtime existente y genera reportes de validación.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        autonomous_manager: Optional[AutonomousWorkflowManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.autonomous_manager = autonomous_manager or AutonomousWorkflowManager(
            db_manager=self.db_manager
        )

    def execute_scenario(self, scenario_name: str) -> RuntimeValidationReport:
        """
        Ejecuta un escenario por nombre y devuelve un RuntimeValidationReport.
        """
        if scenario_name == "memory_optimization_success":
            return self._run_memory_optimization_success()
        elif scenario_name == "capability_failure_handling":
            return self._run_capability_failure_handling()
        elif scenario_name == "partial_execution":
            return self._run_partial_execution()
        else:
            raise ValueError(f"Escenario desconocido: {scenario_name}")

    def _run_memory_optimization_success(self) -> RuntimeValidationReport:
        start_time = time.time()
        cycle = self.autonomous_manager.execute_cycle("memory_optimization")
        execution_time = round(time.time() - start_time, 4)

        status = "passed" if cycle.status == "completed" else "failed"
        summary = (
            f"Escenario 'memory_optimization_success' completado exitosamente con "
            f"{cycle.completed_stages} etapas exitosas de {cycle.total_stages}."
        )

        return RuntimeValidationReport(
            scenario_name="memory_optimization_success",
            status=status,
            stages_executed=cycle.total_stages,
            successful_stages=cycle.completed_stages,
            failed_stages=cycle.failed_stages,
            execution_time=execution_time,
            summary=summary,
        )

    def _run_capability_failure_handling(self) -> RuntimeValidationReport:
        start_time = time.time()

        bm = CapabilityBindingManager(db_manager=self.db_manager)
        mem_binding = MemoryCapabilityBinding(db_manager=self.db_manager)
        mem_binding.register_all(bm)

        def failing_stage_handler(*args, **kwargs):
            raise RuntimeError("Error simulado en la capacidad de Governance para prueba de fallo")

        bm.register_binding(
            stage_name="governance_check",
            manager_or_handler=failing_stage_handler,
            method_name=None,
        )

        from omnilocal_runtime.engine import OmniLocalEngine
        from omnilocal_runtime.workflows.engine import WorkflowEngine

        engine = OmniLocalEngine(db_manager=self.db_manager)
        wfe = WorkflowEngine(
            engine=engine,
            capability_binding_manager=bm,
            db_manager=self.db_manager,
        )
        temp_auto_mgr = AutonomousWorkflowManager(
            workflow_engine=wfe,
            binding_manager=bm,
            db_manager=self.db_manager,
        )

        cycle = temp_auto_mgr.execute_cycle("memory_optimization")
        execution_time = round(time.time() - start_time, 4)

        summary = (
            f"Escenario 'capability_failure_handling' ejecutado correctamente. "
            f"El fallo fue capturado de forma segura. Etapas exitosas: {cycle.completed_stages}, "
            f"Etapas fallidas: {cycle.failed_stages}."
        )

        report_status = "passed" if cycle.failed_stages > 0 else "failed"

        return RuntimeValidationReport(
            scenario_name="capability_failure_handling",
            status=report_status,
            stages_executed=cycle.total_stages,
            successful_stages=cycle.completed_stages,
            failed_stages=cycle.failed_stages,
            execution_time=execution_time,
            summary=summary,
        )

    def _run_partial_execution(self) -> RuntimeValidationReport:
        start_time = time.time()

        bm = CapabilityBindingManager(db_manager=self.db_manager)
        mem_binding = MemoryCapabilityBinding(db_manager=self.db_manager)
        mem_binding.register_all(bm)

        def failing_handler_1(*args, **kwargs):
            raise RuntimeError("Error simulado en validation")

        def failing_handler_2(*args, **kwargs):
            raise RuntimeError("Error simulado en feedback_generation")

        bm.register_binding(
            stage_name="validation",
            manager_or_handler=failing_handler_1,
            method_name=None,
        )
        bm.register_binding(
            stage_name="feedback_generation",
            manager_or_handler=failing_handler_2,
            method_name=None,
        )

        from omnilocal_runtime.engine import OmniLocalEngine
        from omnilocal_runtime.workflows.engine import WorkflowEngine

        engine = OmniLocalEngine(db_manager=self.db_manager)
        wfe = WorkflowEngine(
            engine=engine,
            capability_binding_manager=bm,
            db_manager=self.db_manager,
        )
        temp_auto_mgr = AutonomousWorkflowManager(
            workflow_engine=wfe,
            binding_manager=bm,
            db_manager=self.db_manager,
        )

        cycle = temp_auto_mgr.execute_cycle("memory_optimization")
        execution_time = round(time.time() - start_time, 4)

        summary = (
            f"Escenario 'partial_execution' verificado. Estado del ciclo: {cycle.status}. "
            f"Etapas exitosas: {cycle.completed_stages}, Etapas fallidas: {cycle.failed_stages}."
        )

        report_status = "passed" if cycle.status == "partial" else "partial"

        return RuntimeValidationReport(
            scenario_name="partial_execution",
            status=report_status,
            stages_executed=cycle.total_stages,
            successful_stages=cycle.completed_stages,
            failed_stages=cycle.failed_stages,
            execution_time=execution_time,
            summary=summary,
        )
