from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Modelo de datos para el perfil de un usuario en OmniLocal-Core.
    """
    id: Optional[int] = None
    username: str
    display_name: str
    language: str = "es"
    created_at: datetime = Field(default_factory=datetime.now)


class UserPreference(BaseModel):
    """
    Modelo de datos para una preferencia configurada por el usuario.
    """
    id: Optional[int] = None
    user_id: int
    key: str
    value: str
    created_at: datetime = Field(default_factory=datetime.now)
