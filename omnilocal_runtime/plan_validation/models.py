from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


@dataclass
class RuntimePlanValidationReport:
    """
    Reporte de validación de un plan de ejecución en Runtime (Runtime Block 12).
    Avala o rechaza de manera lógica la propuesta de ejecución antes de cualquier disparo real.
    """
    plan_id: int
    validation_status: str  # approved, approved_with_warnings, rejected
    risk_level: str  # low, medium, high, critical
    checks_performed: str = "[]"
    failed_checks: str = "[]"
    recommendation: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        try:
            data["checks_performed"] = json.loads(self.checks_performed)
        except Exception:
            pass
        try:
            data["failed_checks"] = json.loads(self.failed_checks)
        except Exception:
            pass
        return data


@dataclass
class RuntimePlanSimulationResult:
    """
    Resultado de la simulación hipotética de un plan de ejecución (Runtime Block 12).
    Evalúa la probabilidad de éxito y los posibles fallos sin alterar el sistema.
    """
    plan_id: int
    simulation_status: str  # success, partial, failure
    predicted_outcome: str = ""
    predicted_issues: str = ""
    confidence: float = 0.0
    id: Optional[int] = None
    created_at: Optional[str] = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
