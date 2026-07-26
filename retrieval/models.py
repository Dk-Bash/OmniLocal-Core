from typing import Optional
from pydantic import BaseModel


class RetrievalResult(BaseModel):
    """
    Modelo Pydantic que representa un resultado de búsqueda o recuperación de información.
    """
    id: Optional[int] = None
    source_type: str
    content: str
    score: float = 1.0
