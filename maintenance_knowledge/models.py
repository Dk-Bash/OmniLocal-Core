from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class KnowledgeEntry(BaseModel):
    """Modelo Pydantic que representa una entrada de conocimiento extraído de mantenimiento."""

    id: Optional[int] = Field(
        default=None, description="ID único del registro de conocimiento (asignado por la base de datos)"
    )
    source_feedback_id: int = Field(
        ..., description="ID de la retroalimentación de origen"
    )
    knowledge_type: str = Field(
        ..., description="Tipo de conocimiento ('success_pattern', 'failure_pattern', 'improvement_hint')"
    )
    description: str = Field(
        default="", description="Descripción del conocimiento extraído"
    )
    confidence: float = Field(
        ..., description="Nivel de confianza de la extracción (0.0 a 1.0)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de extracción"
    )

    @validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("El nivel de confianza debe estar entre 0.0 y 1.0 inclusive.")
        return v

    @validator("knowledge_type")
    def validate_knowledge_type(cls, v: str) -> str:
        valid_types = {"success_pattern", "failure_pattern", "improvement_hint"}
        if v not in valid_types:
            raise ValueError(f"Tipo de conocimiento '{v}' no válido. Debe ser uno de {valid_types}.")
        return v
