from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class MaintenancePattern(BaseModel):
    """Modelo Pydantic que representa un patrón reconocido de mantenimiento."""

    id: Optional[int] = Field(
        default=None, description="ID único del patrón (asignado por la base de datos)"
    )
    pattern_type: str = Field(
        ..., description="Tipo de patrón ('frequent_success', 'frequent_failure', 'recurring_issue')"
    )
    occurrences: int = Field(
        default=1, description="Número de ocurrencias asociadas al patrón"
    )
    confidence: float = Field(
        ..., description="Nivel de confianza del patrón (0.0 a 1.0)"
    )
    description: str = Field(
        default="", description="Descripción detallada del patrón"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de detección"
    )

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("El nivel de confianza debe estar entre 0.0 y 1.0 inclusive.")
        return v

    @validator("pattern_type")
    def validate_pattern_type(cls, v: str) -> str:
        valid_types = {"frequent_success", "frequent_failure", "recurring_issue"}
        if v not in valid_types:
            raise ValueError(f"Tipo de patrón '{v}' no válido. Debe ser uno de {valid_types}.")
        return v
