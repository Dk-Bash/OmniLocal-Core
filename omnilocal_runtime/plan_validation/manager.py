from typing import Optional, List, Dict, Any
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.planning.manager import RuntimePlanningManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.plan_validation.models import RuntimePlanValidationReport, RuntimePlanSimulationResult
from omnilocal_runtime.plan_validation.simulator import RuntimePlanSimulator
from omnilocal_runtime.plan_validation.validator import RuntimePlanValidator


class RuntimePlanValidationManager:
    """
    Gestor de Validación y Simulación de Planes para Runtime (Runtime Block 12).
    Coordina la simulación hipotética y la validación lógica de planes de ejecución autónomos
    sin modificar planes originales, ni decisiones pasadas, ni ejecutar acciones reales.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        planning_manager: Optional[RuntimePlanningManager] = None,
        knowledge_manager: Optional[RuntimeKnowledgeManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.planning_manager = planning_manager or RuntimePlanningManager(db_manager=self.db_manager)
        self.knowledge_manager = knowledge_manager or RuntimeKnowledgeManager(db_manager=self.db_manager)
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)

    def simulate(
        self,
        plan_id: Optional[int] = None,
        current_metrics: Optional[Dict[str, Any]] = None
    ) -> RuntimePlanSimulationResult:
        """
        Recupera o genera un plan, ejecuta su simulación hipotética y la persiste en SQLite.
        """
        # 1. Obtener o crear el plan
        plan_dict = None
        if plan_id is not None:
            plan_dict = self.planning_manager.get_plan(plan_id)

        if plan_dict is None:
            plan_obj = self.planning_manager.create_plan(current_metrics=current_metrics)
            plan_dict = plan_obj.to_dict()

        # 2. Ejecutar la simulación con el Simulator
        metrics = current_metrics or self.obs_manager.generate_performance_report().to_dict()
        sim_result = RuntimePlanSimulator.simulate_plan(plan_dict, observability_metrics=metrics)

        # 3. Persistir el resultado en SQLite
        inserted_id = self.db_manager.insert_plan_simulation(
            plan_id=sim_result.plan_id,
            simulation_status=sim_result.simulation_status,
            predicted_outcome=sim_result.predicted_outcome,
            predicted_issues=sim_result.predicted_issues,
            confidence=sim_result.confidence
        )
        sim_result.id = inserted_id

        return sim_result

    def validate(
        self,
        plan_id: Optional[int] = None,
        simulation_result: Optional[RuntimePlanSimulationResult] = None,
        current_metrics: Optional[Dict[str, Any]] = None
    ) -> RuntimePlanValidationReport:
        """
        Simula y valida un plan de ejecución, produciendo un dictamen de aprobación/rechazo persistido.
        """
        # 1. Obtener o crear el plan
        plan_dict = None
        if plan_id is not None:
            plan_dict = self.planning_manager.get_plan(plan_id)

        if plan_dict is None:
            plan_obj = self.planning_manager.create_plan(current_metrics=current_metrics)
            plan_dict = plan_obj.to_dict()

        target_plan_id = plan_dict.get("id", 0)

        # 2. Obtener o generar simulación previa
        if simulation_result is None:
            simulation_result = self.simulate(plan_id=target_plan_id, current_metrics=current_metrics)

        # 3. Obtener conocimiento para validación cruzada
        knowledge_entries = self.knowledge_manager.get_knowledge_entries()

        # 4. Validar el plan con el Validator
        validation_report = RuntimePlanValidator.validate_plan(
            plan=plan_dict,
            simulation_result=simulation_result,
            knowledge_entries=knowledge_entries
        )

        # 5. Persistir el reporte de validación en SQLite
        inserted_id = self.db_manager.insert_plan_validation(
            plan_id=validation_report.plan_id,
            validation_status=validation_report.validation_status,
            risk_level=validation_report.risk_level,
            checks_performed=validation_report.checks_performed,
            failed_checks=validation_report.failed_checks,
            recommendation=validation_report.recommendation
        )
        validation_report.id = inserted_id

        return validation_report

    def get_simulation_result(self, simulation_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un resultado de simulación por su ID."""
        return self.db_manager.get_plan_simulation(simulation_id)

    def get_simulation_results(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de todas las simulaciones de planes."""
        return self.db_manager.get_plan_simulations()

    def get_validation_report(self, validation_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un reporte de validación por su ID."""
        return self.db_manager.get_plan_validation(validation_id)

    def get_validation_reports(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de todas las validaciones de planes."""
        return self.db_manager.get_plan_validations()
