from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ControlOptimizationReport:
    """Módulo 51: Modelo de Optimización de Control Autónomo de Mantenimiento."""
    compliance_id: int
    optimization_status: str
    improvement_area: str
    confidence: float
    recommendation: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_statuses = {"optimized", "stable", "needs_improvement"}
        if self.optimization_status not in allowed_statuses:
            raise ValueError(
                f"optimization_status must be one of {allowed_statuses}, got '{self.optimization_status}'"
            )

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be a float between 0.0 and 1.0, got '{self.confidence}'"
            )
