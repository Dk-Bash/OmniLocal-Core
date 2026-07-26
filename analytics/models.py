from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """
    Modelo Pydantic para representar métricas del sistema.
    """
    total_memories: int = Field(0, description="Cantidad de registros en la tabla memories")
    total_sessions: int = Field(0, description="Cantidad de registros en la tabla context_sessions")
    total_interactions: int = Field(0, description="Cantidad de interacciones (memorias episódicas)")
    average_feedback_score: float = Field(0.0, description="Promedio de valoración en interaction_feedback")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
