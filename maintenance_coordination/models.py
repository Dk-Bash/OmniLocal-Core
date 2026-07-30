from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class CoordinationResult:
    """Módulo 45: Modelo de Resultado de Coordinación Autónoma de Mantenimiento."""
    workflow_id: int
    policy_id: int
    coordination_status: str
    next_action: str
    summary: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_statuses = {"ready", "waiting", "blocked", "completed"}
        if self.coordination_status not in allowed_statuses:
            raise ValueError(
                f"coordination_status must be one of {allowed_statuses}, got '{self.coordination_status}'"
            )
