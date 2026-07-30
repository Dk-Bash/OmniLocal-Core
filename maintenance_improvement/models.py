from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ImprovementRecommendation(BaseModel):
    """Modelo Pydantic que representa una recomendación de mejora continua."""

    id: Optional[int] = Field(
        default=None, description="ID único de la recomendación (asignado por la base de datos)"
    )
    pattern_id: int = Field(
        ..., description="ID del patrón detectado de origen"
    )
    recommendation_type: str = Field(
        ..., description="Tipo de recomendación ('optimization', 'prevention', 'correction')"
    )
    priority: str = Field(
        ..., description="Prioridad de ejecución ('high', 'medium', 'low')"
    )
    description: str = Field(
        default="", description="Descripción detallada de la recomendación de mejora"
    )
    confidence: float = Field(
        ..., description="Nivel de confianza de la recomendación (0.0 a 1.0)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de generación"
    )

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("El nivel de confianza debe estar entre 0.0 y 1.0 inclusive.")
        return v

    @validator("recommendation_type")
    def validate_recommendation_type(cls, v: str) -> str:
        valid_types = {"optimization", "prevention", "correction"}
        if v not in valid_types:
            raise ValueError(f"Tipo de recomendación '{v}' no válido. Debe ser uno de {valid_types}.")
        return v

    @validator("priority")
    def validate_priority(cls, v: str) -> str:
        valid_priorities = {"high", "medium", "low"}
        if v not in valid_priorities:
            raise ValueError(f"Prioridad '{v}' no válida. Debe ser una de {valid_priorities}.")
        return v
