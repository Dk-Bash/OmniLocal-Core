from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MaintenanceDecision(BaseModel):
    """
    Modelo de datos para la Decisión Inteligente de Mantenimiento (Módulo 30).
    Consolida recomendaciones adaptativas, aprendizaje histórico y métricas de inteligencia
    para responder cuál es la mejor decisión de mantenimiento basada en todo el conocimiento disponible.
    """

    id: Optional[int] = None
    decision_type: str = Field(
        ..., description="Tipo de decisión generada ('adaptive', 'default', etc.)"
    )
    selected_strategy: str = Field(
        ..., description="Estrategia seleccionada (ej. immediate, soon, planned, unknown)"
    )
    confidence: float = Field(
        ..., description="Nivel de confianza de la decisión (0.0 a 1.0)"
    )
    reasoning: str = Field(
        ..., description="Explicación fundamentada y justificativa de la decisión"
    )
    supporting_factors: List[str] = Field(
        default_factory=list,
        description="Lista de factores de soporte que justifican la decisión"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha y hora de generación de la decisión"
    )
