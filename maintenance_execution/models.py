from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MaintenanceExecutionPlan(BaseModel):
    """
    Modelo de datos para el Plan de Ejecución de Mantenimiento (Módulo 31).
    Transforma una decisión inteligente en un plan de ejecución controlado.
    No ejecuta acciones reales ni modifica datos existentes.
    """

    id: Optional[int] = None
    decision_type: str = Field(
        ..., description="Tipo de decisión evaluada ('adaptive', 'default', etc.)"
    )
    strategy_type: str = Field(
        ..., description="Estrategia asociada ('immediate', 'soon', 'planned', 'unknown', etc.)"
    )
    execution_steps: List[str] = Field(
        default_factory=list,
        description="Pasos detallados de ejecución del plan"
    )
    risk_level: str = Field(
        ..., description="Nivel de riesgo estimado ('low', 'medium', 'high', etc.)"
    )
    estimated_duration: str = Field(
        ..., description="Duración estimada del plan (ej. '15m', '0m')"
    )
    requires_approval: bool = Field(
        default=False,
        description="Indica si el plan de ejecución requiere aprobación manual previa"
    )
    reasoning: str = Field(
        default="",
        description="Explicación y justificación técnica del plan de ejecución"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha y hora de generación del plan"
    )
