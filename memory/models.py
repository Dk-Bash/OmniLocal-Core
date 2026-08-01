from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from pydantic import BaseModel, Field
    try:
        from pydantic import field_validator
    except ImportError:
        from pydantic import validator as field_validator
except ImportError:
    class ValidationError(Exception):
        pass

    def Field(default=None, default_factory=None, ge=None, le=None, **kwargs):
        return {
            "__is_field__": True,
            "default": default,
            "default_factory": default_factory,
            "ge": ge,
            "le": le,
        }

    def field_validator(*fields, **kwargs):
        def decorator(fn):
            fn.__is_field_validator__ = True
            fn.__validator_fields__ = fields
            return classmethod(fn)
        return decorator

    class BaseModel:
        def __init__(self, **data):
            cls = self.__class__
            annotations = getattr(cls, "__annotations__", {})
            for name in annotations.keys():
                if name in data:
                    val = data[name]
                elif hasattr(cls, name):
                    class_attr = getattr(cls, name)
                    if isinstance(class_attr, dict) and class_attr.get("__is_field__"):
                        if class_attr.get("default_factory") is not None:
                            val = class_attr["default_factory"]()
                        else:
                            val = class_attr.get("default")
                    else:
                        val = class_attr
                else:
                    val = None
                setattr(self, name, val)

            for attr_name in dir(cls):
                try:
                    attr = getattr(cls, attr_name, None)
                except Exception:
                    continue
                if callable(attr) and getattr(attr, "__is_field_validator__", False):
                    validator_fields = getattr(attr, "__validator_fields__", [])
                    for f_name in validator_fields:
                        f_val = getattr(self, f_name, None)
                        if f_val is not None:
                            try:
                                unwrapped = getattr(attr, "__func__", attr)
                                new_val = unwrapped(cls, f_val)
                                setattr(self, f_name, new_val)
                            except ValueError as ve:
                                raise ValidationError(str(ve))

        def dict(self, *args, **kwargs) -> Dict[str, Any]:
            res = {}
            annotations = getattr(self.__class__, "__annotations__", {})
            for k in annotations.keys():
                v = getattr(self, k, None)
                if hasattr(v, "dict"):
                    res[k] = v.dict()
                elif isinstance(v, list):
                    res[k] = [item.dict() if hasattr(item, "dict") else item for item in v]
                else:
                    res[k] = v
            return res

        def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
            return self.dict(*args, **kwargs)


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

    Bloque 6 (Adaptive Memory Consolidation): `confidence` es distinto de
    `importance` -- importancia es cuánto pesa en el ranking (Bloque 3);
    confianza es qué tan seguro está el sistema de que el dato sigue
    vigente (por ahora siempre 1.0 al detectarse por reglas, que son
    determinísticas; queda la puerta abierta para que feedback futuro la
    ajuste sin tocar el ranking). `updated_at` distingue "cuándo se creó"
    de "cuándo se confirmó/corrigió por última vez".
    """
    id: Optional[int] = None
    content: str
    memory_type: str = "episodic"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

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
