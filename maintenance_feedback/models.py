from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ExecutionFeedback(BaseModel):
    """Modelo Pydantic que representa la retroalimentación de una ejecución de mantenimiento."""

    id: Optional[int] = Field(
        default=None, description="ID único del feedback (asignado por la base de datos)"
    )
    result_id: int = Field(
        ..., description="ID del resultado de ejecución asociado"
    )
    feedback_type: str = Field(
        ..., description="Tipo de retroalimentación ('positive', 'neutral', 'negative')"
    )
    quality_score: float = Field(
        ..., description="Puntuación de calidad asignada (0.0 a 1.0)"
    )
    learning_notes: str = Field(
        default="", description="Notas o lecciones para el sistema de aprendizaje"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de registro del feedback"
    )

    @validator("feedback_type")
    def validate_feedback_type(cls, v: str) -> str:
        valid_types = {"positive", "neutral", "negative"}
        if v not in valid_types:
            raise ValueError(f"Tipo de feedback '{v}' no válido. Debe ser uno de {valid_types}.")
        return v

    @validator("quality_score")
    def validate_quality_score(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("La puntuación de calidad debe estar entre 0.0 y 1.0 inclusive.")
        return v
