from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class InteractionResult(BaseModel):
    """
    Modelo de resultado de una interacción procesada por OrchestratorEngine.
    Representa la respuesta estructurada de la coordinación entre contextos,
    búsquedas personalizadas y registros de memoria.
    """
    id: Optional[int] = None
    query: str
    results_count: int
    sources: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
