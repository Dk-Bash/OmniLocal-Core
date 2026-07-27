from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StrategyRecommendation(BaseModel):
    """
    Modelo Pydantic para recomendaciones estratégicas de mantenimiento (Módulo 26).
    """

    id: Optional[int] = None
    task_type: str
    recommended_priority: str
    reason: str
    expected_benefit: float
    created_at: datetime = Field(default_factory=datetime.now)
