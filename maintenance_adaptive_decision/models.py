from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class AdaptiveDecision:
    """Módulo 41: Modelo de Decisión Adaptativa de Mantenimiento."""
    correlation_id: int
    decision_type: str
    recommended_strategy: str
    confidence: float
    reasoning: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        allowed_types = {"adaptive", "conservative", "fallback"}
        if self.decision_type not in allowed_types:
            raise ValueError(
                f"decision_type must be one of {allowed_types}, got '{self.decision_type}'"
            )
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
