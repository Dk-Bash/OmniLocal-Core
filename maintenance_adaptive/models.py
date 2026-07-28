from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AdaptiveRecommendation(BaseModel):
    """
    Modelo de datos para la recomendación adaptativa de estrategia de mantenimiento (Módulo 29).
    Sintetiza aprendizaje histórico y condiciones actuales para responder
    qué estrategia conviene aplicar en el momento actual.
    """

    id: Optional[int] = None
    strategy_type: str = Field(
        ..., description="Tipo de estrategia recomendada (ej. immediate, soon, planned, deferred, unknown)"
    )
    recommended_action: str = Field(
        ..., description="Acción recomendada basada en el aprendizaje histórico"
    )
    confidence: float = Field(
        ..., description="Nivel de confianza de la recomendación adaptativa (0.0 a 1.0)"
    )
    reason: str = Field(
        ..., description="Justificación detallada de la recomendación"
    )
    based_on_history: bool = Field(
        ..., description="Indica si la recomendación se fundamenta en aprendizaje previo"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de generación de la recomendación"
    )
