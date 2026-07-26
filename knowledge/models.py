from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeNode(BaseModel):
    """
    Modelo Pydantic que representa una entidad o nodo de conocimiento.
    """
    id: Optional[int] = None
    name: str
    node_type: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class KnowledgeRelation(BaseModel):
    """
    Modelo Pydantic que representa una relación entre dos nodos de conocimiento.
    """
    id: Optional[int] = None
    source_id: int
    target_id: int
    relation_type: str
    created_at: datetime = Field(default_factory=datetime.now)
