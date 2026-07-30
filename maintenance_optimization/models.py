from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class OptimizationFeedback:
    """Módulo 42: Modelo de Retroalimentación de Optimización Continua."""
    decision_id: int
    previous_confidence: float
    new_confidence: float
    improvement_score: float
    optimization_type: str
    summary: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_types = {"improved", "stable", "degraded"}
        if self.optimization_type not in allowed_types:
            raise ValueError(
                f"optimization_type must be one of {allowed_types}, got '{self.optimization_type}'"
            )
        if not (0.0 <= float(self.previous_confidence) <= 1.0):
            raise ValueError(f"previous_confidence must be between 0.0 and 1.0, got {self.previous_confidence}")
        if not (0.0 <= float(self.new_confidence) <= 1.0):
            raise ValueError(f"new_confidence must be between 0.0 and 1.0, got {self.new_confidence}")
