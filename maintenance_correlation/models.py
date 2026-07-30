from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any


@dataclass
class IntelligenceCorrelation:
    """Módulo 40: Modelo de Correlación de Inteligencia de Mantenimiento."""
    strategy_type: str
    pattern_type: str
    success_rate: float
    sample_size: int
    confidence: float
    description: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if not (0.0 <= float(self.success_rate) <= 1.0):
            raise ValueError(f"success_rate must be between 0.0 and 1.0, got {self.success_rate}")
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        if int(self.sample_size) < 0:
            raise ValueError(f"sample_size cannot be negative, got {self.sample_size}")
