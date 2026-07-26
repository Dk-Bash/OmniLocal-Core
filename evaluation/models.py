from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

try:
    from pydantic import field_validator

    class InteractionFeedback(BaseModel):
        """
        Modelo Pydantic para representar evaluaciones y feedback de interacciones.
        """
        id: Optional[int] = None
        interaction_id: int
        rating: int = Field(..., ge=1, le=5, description="Valoración entera entre 1 y 5")
        confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza flotante entre 0.0 y 1.0")
        comment: str = ""
        created_at: Optional[datetime] = Field(default_factory=datetime.now)

        @field_validator("rating")
        @classmethod
        def validate_rating(cls, v: int) -> int:
            if v < 1 or v > 5:
                raise ValueError("rating debe estar entre 1 y 5")
            return v

        @field_validator("confidence")
        @classmethod
        def validate_confidence(cls, v: float) -> float:
            if v < 0.0 or v > 1.0:
                raise ValueError("confidence debe estar entre 0.0 y 1.0")
            return v
except ImportError:
    from pydantic import validator

    class InteractionFeedback(BaseModel): # type: ignore
        """
        Modelo Pydantic para representar evaluaciones y feedback de interacciones (Pydantic v1 fallback).
        """
        id: Optional[int] = None
        interaction_id: int
        rating: int = Field(..., ge=1, le=5, description="Valoración entera entre 1 y 5")
        confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza flotante entre 0.0 y 1.0")
        comment: str = ""
        created_at: Optional[datetime] = Field(default_factory=datetime.now)

        @validator("rating")
        def validate_rating(cls, v: int) -> int:
            if v < 1 or v > 5:
                raise ValueError("rating debe estar entre 1 y 5")
            return v

        @validator("confidence")
        def validate_confidence(cls, v: float) -> float:
            if v < 0.0 or v > 1.0:
                raise ValueError("confidence debe estar entre 0.0 y 1.0")
            return v
