from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ExecutionApproval(BaseModel):
    """Modelo Pydantic que representa la aprobación formal de un plan de ejecución validado."""

    id: Optional[int] = Field(
        default=None, description="ID único del registro de aprobación (asignado por la base de datos)"
    )
    plan_id: int = Field(
        ..., description="ID del plan de ejecución evaluado"
    )
    validation_id: int = Field(
        ..., description="ID del reporte de validación asociado"
    )
    approval_status: str = Field(
        ..., description="Estado de aprobación ('approved', 'rejected', 'requires_review')"
    )
    approved: bool = Field(
        ..., description="Booleano que indica si la ejecución está formalmente autorizada"
    )
    reason: str = Field(
        ..., description="Explicación detallada de la decisión de aprobación"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de registro de la aprobación"
    )
