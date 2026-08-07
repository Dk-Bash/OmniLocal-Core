from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Goal(BaseModel):
    """
    Modelo Pydantic que representa un objetivo/recordatorio del usuario.

    Bloque 9 (Foundation): guardar, listar, completar -- solo texto libre.
    Bloque 10 (Understanding & Management): se agregan `description`,
    `goal_type` y `category` para estructurar el objetivo. `content` se
    mantiene tal cual (decisión explícita: no renombrar a `title`, para no
    romper compatibilidad con el Bloque 9) -- cumple el rol de título
    corto. `category` queda listo en el esquema pero sin lógica de
    inferencia todavía (se guarda `None` a propósito).

    El "cuándo avisar solo" (scheduler) sigue fuera de alcance, para un
    bloque futuro con su propia auditoría.
    """
    id: Optional[int] = None
    content: str
    description: Optional[str] = None
    goal_type: str = "task"
    category: Optional[str] = None
    due_at: Optional[datetime] = None
    status: str = "pendiente"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
