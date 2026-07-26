from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContextSession(BaseModel):
    """
    Modelo Pydantic que representa una sesión de contexto conversacional.
    """
    id: Optional[int] = None
    session_name: str
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class ContextMessage(BaseModel):
    """
    Modelo Pydantic que representa un mensaje dentro de una sesión de contexto.
    """
    id: Optional[int] = None
    session_id: int
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
