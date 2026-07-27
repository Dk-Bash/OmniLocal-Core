from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StrategyEvaluation(BaseModel):
    """
    Modelo de datos para la evaluación de estrategias de mantenimiento (Módulo 27).
    """

    id: Optional[int] = None
    strategy_id: str
    quality_score: float
    impact_score: float
    confidence_score: float
    summary: str
    created_at: datetime = Field(default_factory=datetime.now)
