from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    """
    Modelo Pydantic que representa un proyecto de trabajo del usuario
    (Bloque 14 -- Project Workspace Foundation).

    Entidad independiente a propósito: no tiene todavía ningún vínculo
    con `Goal`/`Memory`/`KnowledgeNode`, pero está diseñada para poder
    relacionarse en el futuro (via `id`) sin necesidad de rediseñar nada
    -- esa integración real queda para un bloque aparte, cuando "Proyecto"
    ya esté probado solo.

    `status_summary` es la única parte que puede involucrar al modelo de
    IA, y solo bajo demanda (nunca automático al escanear) -- ver
    local_ai/project_scanner.py.
    """
    id: Optional[int] = None
    name: str
    path: str
    objective: Optional[str] = None
    technologies: Optional[str] = None
    structure_summary: Optional[str] = None
    status_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_indexed_at: Optional[datetime] = None
