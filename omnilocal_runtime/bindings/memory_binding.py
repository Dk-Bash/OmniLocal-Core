from typing import Optional, Any
from database.sqlite_manager import SQLiteManager
from memory_analysis.manager import MemoryAnalysisManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.manager import MemoryPriorityManager
from memory_governance.manager import GovernanceManager
from memory_simulation.manager import SimulationManager
from omnilocal_runtime.bindings.manager import CapabilityBindingManager


# Aliases convenientes según especificación del Runtime Block 03
MemoryIntelligenceManager = MemoryAnalysisManager
MemorySimulationManager = SimulationManager


class MemoryCapabilityBinding:
    """
    Binding de capacidades de memoria para OmniLocal Runtime (Runtime Block 03).
    Conecta las etapas del workflow de optimización de memoria con los managers reales existentes:
      - memory_analysis     -> MemoryAnalysisManager (MemoryIntelligenceManager)
      - priority_evaluation -> MemoryPriorityManager
      - simulation          -> SimulationManager (MemorySimulationManager)
    
    Respeta la regla fundamental: NO modifica lógica ni datos existentes.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        intelligence_manager: Optional[MemoryAnalysisManager] = None,
        priority_manager: Optional[MemoryPriorityManager] = None,
        simulation_manager: Optional[SimulationManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()

        self.intelligence_manager = intelligence_manager or MemoryAnalysisManager(db_manager=self.db_manager)

        if not priority_manager:
            integrity_mgr = MemoryIntegrityManager(db_manager=self.db_manager)
            maint_mgr = MaintenanceManager(integrity_manager=integrity_mgr)
            plan_mgr = MaintenancePlanningManager(maintenance_manager=maint_mgr)
            self.priority_manager = MemoryPriorityManager(planning_manager=plan_mgr)
        else:
            self.priority_manager = priority_manager

        if not simulation_manager:
            gov_mgr = GovernanceManager(priority_manager=self.priority_manager)
            self.simulation_manager = SimulationManager(governance_manager=gov_mgr)
        else:
            self.simulation_manager = simulation_manager

    def register_all(self, binding_manager: CapabilityBindingManager) -> None:
        """Registra las 3 etapas principales en el CapabilityBindingManager especificado."""
        binding_manager.register_binding(
            stage_name="memory_analysis",
            manager_or_handler=self.intelligence_manager,
            method_name="analyze_memory",
        )
        binding_manager.register_binding(
            stage_name="priority_evaluation",
            manager_or_handler=self.priority_manager,
            method_name="prioritize",
        )
        binding_manager.register_binding(
            stage_name="simulation",
            manager_or_handler=self.simulation_manager,
            method_name="simulate",
        )
