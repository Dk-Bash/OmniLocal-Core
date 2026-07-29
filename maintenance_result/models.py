from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ExecutionResult(BaseModel):
    """Modelo Pydantic que representa el resultado de una ejecución de mantenimiento."""

    id: Optional[int] = Field(
        default=None, description="ID único del resultado (asignado por la base de datos)"
    )
    tracking_id: int = Field(
        ..., description="ID del registro de seguimiento de ejecución asociado"
    )
    result_status: str = Field(
        ..., description="Estado del resultado ('success', 'failed', 'partial')"
    )
    impact: str = Field(
        ..., description="Impacto determinado ('positive', 'neutral', 'negative')"
    )
    summary: str = Field(
        default="", description="Resumen descriptivo del resultado"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de registro del resultado"
    )

    @validator("result_status")
    def validate_result_status(cls, v: str) -> str:
        valid_statuses = {"success", "failed", "partial"}
        if v not in valid_statuses:
            raise ValueError(f"Estado de resultado '{v}' no válido. Debe ser uno de {valid_statuses}.")
        return v

    @validator("impact")
    def validate_impact(cls, v: str) -> str:
        valid_impacts = {"positive", "neutral", "negative"}
        if v not in valid_impacts:
            raise ValueError(f"Impacto '{v}' no válido. Debe ser uno de {valid_impacts}.")
        return v
