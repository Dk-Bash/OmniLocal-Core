from typing import Optional
from pydantic import BaseModel, Field


class PersonalizedResult(BaseModel):
    """
    Modelo de resultado para búsquedas personalizadas en OmniLocal-Core.
    Combina información de recuperación básica con ajustes de relevancia por usuario y contexto.
    """
    id: Optional[int] = None
    source_type: str
    content: str
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str
