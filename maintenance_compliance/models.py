from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ComplianceReport:
    """Módulo 50: Modelo de Validación de Cumplimiento Normativo de Mantenimiento."""
    governance_id: int
    compliant: bool
    violations: str
    compliance_score: float
    recommendation: str
    id: Optional[int] = None
    created_at: Optional[Any] = None

    def __post_init__(self):
        if not (0.0 <= self.compliance_score <= 1.0):
            raise ValueError(
                f"compliance_score must be a float between 0.0 and 1.0, got '{self.compliance_score}'"
            )
