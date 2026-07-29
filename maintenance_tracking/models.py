from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ExecutionTracking(BaseModel):
    """Modelo Pydantic que representa el seguimiento de ejecución de un mantenimiento."""

    id: Optional[int] = Field(
        default=None, description="ID único del registro de seguimiento (asignado por la base de datos)"
    )
    approval_id: int = Field(
        ..., description="ID del registro de aprobación formal asociado"
    )
    status: str = Field(
        default="pending", description="Estado actual de ejecución ('pending', 'running', 'completed', 'failed', 'cancelled')"
    )
    progress: float = Field(
        default=0.0, description="Progreso de la ejecución (0.0 a 1.0)"
    )
    message: str = Field(
        default="", description="Mensaje o detalle del estado del seguimiento"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de creación del seguimiento"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de última actualización del seguimiento"
    )

    @validator("progress")
    def validate_progress(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("El progreso debe estar entre 0.0 y 1.0 inclusive.")
        return v

    @validator("status")
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"pending", "running", "completed", "failed", "cancelled"}
        if v not in valid_statuses:
            raise ValueError(f"Estado no válido '{v}'. Debe ser uno de {valid_statuses}.")
        return v
