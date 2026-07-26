from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator


class User(BaseModel):
    """
    Modelo Pydantic que representa a un usuario del sistema.
    """
    id: Optional[int] = None
    name: str
    created_at: datetime = Field(default_factory=datetime.now)


class Memory(BaseModel):
    """
    Modelo Pydantic que representa una entidad de recuerdo en el sistema.
    La importancia debe estar comprendida estrictamente entre 0.0 y 1.0.
    """
    id: Optional[int] = None
    content: str
    memory_type: str = "episodic"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("importance")
    def validate_importance(cls, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"La importancia debe estar entre 0.0 y 1.0. Se recibió: {value}")
        return value


class Conversation(BaseModel):
    """
    Modelo Pydantic que representa una interacción conversacional.
    """
    id: Optional[int] = None
    user_input: str
    assistant_response: str
    created_at: datetime = Field(default_factory=datetime.now)
