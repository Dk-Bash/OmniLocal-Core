from typing import Optional, List
from memory_governance.manager import GovernanceManager
from memory_simulation.models import SimulationResult


class SimulationManager:
    """Capa de simulación de mantenimiento de memoria para OmniLocal-Core (Módulo 22)."""

    def __init__(self, governance_manager: Optional[GovernanceManager] = None):
        self.governance_manager = governance_manager or GovernanceManager()

    def simulate(self) -> List[SimulationResult]:
        """Ejecuta GovernanceManager.evaluate_tasks() y simula los resultados sin modificar datos reales."""
        approvals = self.governance_manager.evaluate_tasks()
        results: List[SimulationResult] = []

        for app in approvals:
            if app.approval_status == "approved":
                status = "simulated"
                if app.task_type == "duplicate_review":
                    impact = "Reducir posibles duplicados y redundancia de memoria"
                else:
                    impact = "Optimizar memoria con bajo riesgo"
                details = "Simulación realizada con éxito. No se realizaron modificaciones reales."
            else:
                status = "blocked"
                impact = "Revisión requerida antes de modificar"
                details = f"Acción de tipo '{app.task_type}' bloqueada por requerir aprobación previa (nivel de riesgo: {app.risk_level})."

            results.append(
                SimulationResult(
                    id=app.id,
                    task_type=app.task_type,
                    simulation_status=status,
                    expected_impact=impact,
                    details=details
                )
            )

        return results
