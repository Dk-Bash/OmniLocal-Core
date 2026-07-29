from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ExecutionValidationReport(BaseModel):
    """Modelo Pydantic que representa el reporte de validación previa de un plan de ejecución."""

    id: Optional[int] = Field(
        default=None, description="ID único del reporte de validación (asignado por la base de datos)"
    )
    plan_id: int = Field(
        ..., description="ID del plan de ejecución verificado"
    )
    valid: bool = Field(
        ..., description="Indica si el plan de ejecución es válido para proceder"
    )
    risk_level: str = Field(
        ..., description="Nivel de riesgo determinado ('low', 'medium', 'high')"
    )
    issues: List[str] = Field(
        default_factory=list, description="Lista de problemas o requerimientos detectados"
    )
    recommendation: str = Field(
        ..., description="Recomendación o acción sugerida para la ejecución"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de generación del reporte de validación"
    )
