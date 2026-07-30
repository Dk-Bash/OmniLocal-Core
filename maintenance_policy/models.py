from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class MaintenancePolicyResult:
    """Módulo 44: Modelo de Evaluación de Políticas de Mantenimiento."""
    workflow_id: int
    allowed: bool
    risk_level: str
    reasoning: str
    violations: str = ""
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_risks = {"low", "medium", "high"}
        if self.risk_level not in allowed_risks:
            raise ValueError(
                f"risk_level must be one of {allowed_risks}, got '{self.risk_level}'"
            )
