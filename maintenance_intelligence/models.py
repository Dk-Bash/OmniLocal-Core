from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MaintenanceIntelligenceReport(BaseModel):
    """
    Modelo Pydantic para el reporte analítico de inteligencia de mantenimiento (Módulo 25).
    """

    id: Optional[int] = None
    total_events: int = 0
    completed_events: int = 0
    blocked_events: int = 0
    failed_events: int = 0
    average_score: float = 0.0
    most_common_result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
