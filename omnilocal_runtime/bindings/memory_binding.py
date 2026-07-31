from typing import Optional, Any
from database.sqlite_manager import SQLiteManager
from memory_analysis.manager import MemoryAnalysisManager
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.manager import MaintenanceManager
from memory_planning.manager import MaintenancePlanningManager
from memory_priority.manager import MemoryPriorityManager
from memory_governance.manager import GovernanceManager
from memory_simulation.manager import SimulationManager
from maintenance_decision.manager import MaintenanceDecisionManager
from maintenance_execution.manager import MaintenanceExecutionManager
from maintenance_validation.manager import ExecutionValidationManager
from maintenance_feedback.manager import ExecutionFeedbackManager
from maintenance_strategy_learning.manager import StrategyLearningManager
from omnilocal_runtime.bindings.manager import CapabilityBindingManager


# Aliases convenientes según especificación del Runtime Block 03 y 04
MemoryIntelligenceManager = MemoryAnalysisManager
MemorySimulationManager = SimulationManager
MemoryGovernanceManager = GovernanceManager
MaintenanceValidationManager = ExecutionValidationManager
MaintenanceFeedbackManager = ExecutionFeedbackManager


class MemoryCapabilityBinding:
    """
    Binding de capacidades de memoria para OmniLocal Runtime (Runtime Block 03 y 04).
    Conecta las 9 etapas del workflow de optimización de memoria autónomo con los managers reales existentes:
      - memory_analysis     -> MemoryIntelligenceManager (MemoryAnalysisManager)
      - priority_evaluation -> MemoryPriorityManager
      - simulation          -> MemorySimulationManager (SimulationManager)
      - governance_check    -> MemoryGovernanceManager (GovernanceManager)
      - decision_generation -> MaintenanceDecisionManager
      - execution_planning  -> MaintenanceExecutionManager
      - validation          -> MaintenanceValidationManager (ExecutionValidationManager)
      - feedback_generation -> MaintenanceFeedbackManager (ExecutionFeedbackManager)
      - learning_update     -> StrategyLearningManager
    
    Respeta la regla fundamental: NO modifica lógica ni datos existentes.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        intelligence_manager: Optional[MemoryAnalysisManager] = None,
        priority_manager: Optional[MemoryPriorityManager] = None,
        simulation_manager: Optional[SimulationManager] = None,
        governance_manager: Optional[GovernanceManager] = None,
        decision_manager: Optional[MaintenanceDecisionManager] = None,
        execution_manager: Optional[MaintenanceExecutionManager] = None,
        validation_manager: Optional[ExecutionValidationManager] = None,
        feedback_manager: Optional[ExecutionFeedbackManager] = None,
        learning_manager: Optional[StrategyLearningManager] = None,
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

        self.governance_manager = governance_manager or GovernanceManager(priority_manager=self.priority_manager)
        self.decision_manager = decision_manager or MaintenanceDecisionManager(db_manager=self.db_manager)
        self.execution_manager = execution_manager or MaintenanceExecutionManager(
            decision_manager=self.decision_manager,
            db_manager=self.db_manager,
        )
        self.validation_manager = validation_manager or ExecutionValidationManager(
            db_manager=self.db_manager,
            execution_manager=self.execution_manager,
        )
        self.feedback_manager = feedback_manager or ExecutionFeedbackManager(db_manager=self.db_manager)
        self.learning_manager = learning_manager or StrategyLearningManager(db_manager=self.db_manager)

    def register_all(self, binding_manager: CapabilityBindingManager) -> None:
        """Registra las 9 etapas del workflow autónomo en el CapabilityBindingManager especificado."""
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
        binding_manager.register_binding(
            stage_name="governance_check",
            manager_or_handler=self.governance_manager,
            method_name="evaluate_tasks",
        )
        binding_manager.register_binding(
            stage_name="decision_generation",
            manager_or_handler=self.decision_manager,
            method_name="make_decision",
        )
        binding_manager.register_binding(
            stage_name="execution_planning",
            manager_or_handler=self.execution_manager,
            method_name="create_execution_plan",
        )
        binding_manager.register_binding(
            stage_name="validation",
            manager_or_handler=self.validation_manager,
            method_name="validate_plan",
        )
        binding_manager.register_binding(
            stage_name="feedback_generation",
            manager_or_handler=self.feedback_manager,
            method_name="generate_feedback",
        )
        binding_manager.register_binding(
            stage_name="learning_update",
            manager_or_handler=self.learning_manager,
            method_name="generate_learning_report",
        )

