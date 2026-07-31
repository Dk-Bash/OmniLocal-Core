from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.validation.models import RuntimeValidationReport
from omnilocal_runtime.validation.scenarios import ScenarioManager


class RuntimeValidationManager:
    """
    Gestor Principal de Validaciones Runtime End-to-End (Runtime Block 05).
    Coordina la ejecución de escenarios de prueba y persiste sus reportes de validación.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        scenario_manager: Optional[ScenarioManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.scenario_manager = scenario_manager or ScenarioManager(db_manager=self.db_manager)

    def execute_scenario(self, scenario_name: str) -> RuntimeValidationReport:
        """
        Ejecuta un escenario específico, persiste el reporte en SQLite y devuelve el objeto RuntimeValidationReport.
        """
        report = self.scenario_manager.execute_scenario(scenario_name)

        report_id = self.db_manager.insert_runtime_validation_report(
            scenario_name=report.scenario_name,
            status=report.status,
            stages_executed=report.stages_executed,
            successful_stages=report.successful_stages,
            failed_stages=report.failed_stages,
            execution_time=report.execution_time,
            summary=report.summary,
        )

        report.id = report_id
        return report

    def run_validation(self, scenario_name: str = "memory_optimization_success") -> RuntimeValidationReport:
        """
        Alias para execute_scenario, por defecto ejecuta 'memory_optimization_success'.
        """
        return self.execute_scenario(scenario_name)

    def run_all_validations(self) -> List[RuntimeValidationReport]:
        """
        Ejecuta los 3 escenarios principales de validación end-to-end.
        """
        scenarios = [
            "memory_optimization_success",
            "capability_failure_handling",
            "partial_execution",
        ]
        reports = []
        for sc in scenarios:
            rep = self.execute_scenario(sc)
            reports.append(rep)
        return reports

    def get_report(self, report_id: int) -> Optional[RuntimeValidationReport]:
        """Obtiene un reporte de validación por ID desde la base de datos."""
        row = self.db_manager.get_runtime_validation_report(report_id)
        if not row:
            return None
        return RuntimeValidationReport(
            id=row["id"],
            scenario_name=row["scenario_name"],
            status=row["status"],
            stages_executed=row["stages_executed"],
            successful_stages=row["successful_stages"],
            failed_stages=row["failed_stages"],
            execution_time=row["execution_time"],
            summary=row["summary"],
            created_at=row.get("created_at"),
        )

    def get_reports(self) -> List[Dict[str, Any]]:
        """Obtiene todos los reportes de validación registrados."""
        return self.db_manager.get_runtime_validation_reports()
