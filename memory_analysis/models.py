from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class MemoryAnalysis(BaseModel):
    """
    Modelo Pydantic para representar el análisis de memorias existentes (Módulo 16).
    """
    id: Optional[int] = Field(None, description="ID del análisis si fuera registrado")
    total_memories: int = Field(0, description="Cantidad total de recuerdos")
    memory_types: Dict[str, int] = Field(default_factory=dict, description="Distribución de memorias por tipo")
    most_common_type: str = Field("none", description="Tipo de memoria más frecuente")
    average_importance: float = Field(0.0, description="Promedio del campo importance de las memorias")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
