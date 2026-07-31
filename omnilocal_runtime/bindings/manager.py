import json
from typing import Optional, Dict, Any, Union, Callable
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.bindings.models import CapabilityBindingResult


class CapabilityBindingManager:
    """
    Gestor de bindings entre etapas de workflows y capacidades (managers) reales.
    Permite registrar qué manager/función ejecuta cada etapa y guarda los resultados en SQLite.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.registry: Dict[str, Dict[str, Any]] = {}

    def register_binding(
        self,
        stage_name: str,
        manager_or_handler: Any,
        method_name: Optional[str] = None,
    ) -> None:
        """
        Registra un binding entre una etapa (stage_name) y un manager o función ejecutora.
        - manager_or_handler: Instancia de manager, clase o función.
        - method_name: Nombre opcional del método a invocar en la instancia del manager.
        """
        manager_name = (
            getattr(manager_or_handler, "__name__", None)
            or manager_or_handler.__class__.__name__
        )

        self.registry[stage_name] = {
            "manager": manager_or_handler,
            "manager_name": manager_name,
            "method_name": method_name,
        }

    def get_binding(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Devuelve la configuración del binding registrado para la etapa."""
        return self.registry.get(stage_name)

    def _serialize_data(self, obj: Any) -> Any:
        """Convierte objetos retornados por los managers (Pydantic, dataclasses, etc.) a estructuras JSON serializables."""
        if obj is None:
            return None
        if isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: self._serialize_data(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._serialize_data(item) for item in obj]
        if hasattr(obj, "model_dump"):
            return self._serialize_data(obj.model_dump())
        if hasattr(obj, "dict"):
            return self._serialize_data(obj.dict())
        if hasattr(obj, "__dict__"):
            return self._serialize_data(obj.__dict__)
        return str(obj)

    def execute_binding(
        self,
        stage_name: str,
        context: Any = None,
        **kwargs
    ) -> CapabilityBindingResult:
        """
        Ejecuta la capacidad real registrada para la etapa dada.
        Retorna y persiste un CapabilityBindingResult en la base de datos.
        """
        binding = self.get_binding(stage_name)
        if not binding:
            raise ValueError(f"No binding registered for stage '{stage_name}'")

        target = binding["manager"]
        manager_name = binding["manager_name"]
        method_name = binding["method_name"]

        try:
            if callable(target) and not hasattr(target, "__class__") and method_name is None:
                raw_output = target(context, **kwargs)
            elif method_name and hasattr(target, method_name):
                method = getattr(target, method_name)
                import inspect
                try:
                    sig = inspect.signature(method)
                    params = sig.parameters
                    has_context_param = any(p in params for p in ("context", "ctx", "runtime_context"))
                    if has_context_param:
                        raw_output = method(context, **kwargs)
                    elif len(params) == 0:
                        raw_output = method()
                    else:
                        try:
                            raw_output = method(**kwargs)
                        except TypeError:
                            try:
                                raw_output = method()
                            except TypeError:
                                raw_output = method(context, **kwargs)
                except Exception:
                    try:
                        raw_output = method()
                    except TypeError:
                        raw_output = method(context, **kwargs)
            elif hasattr(target, "analyze_memory"):
                raw_output = target.analyze_memory()
            elif hasattr(target, "prioritize"):
                raw_output = target.prioritize()
            elif hasattr(target, "simulate"):
                raw_output = target.simulate()
            elif callable(target):
                try:
                    raw_output = target(context, **kwargs)
                except TypeError:
                    raw_output = target()
            else:
                raise AttributeError(f"Manager '{manager_name}' has no executable method or handler for '{stage_name}'")

            serialized_data = self._serialize_data(raw_output)

            # Generar resumen
            if isinstance(raw_output, dict) and "summary" in raw_output:
                summary = str(raw_output["summary"])
            elif serialized_data and isinstance(serialized_data, dict):
                summary = f"Ejecución exitosa de {manager_name} para la etapa '{stage_name}'."
            elif serialized_data and isinstance(serialized_data, list):
                summary = f"Ejecución de {manager_name} completada. {len(serialized_data)} ítems procesados."
            else:
                summary = f"Ejecución de la capacidad {manager_name} finalizada para '{stage_name}'."

            result_obj = CapabilityBindingResult(
                stage_name=stage_name,
                manager_name=manager_name,
                success=True,
                summary=summary,
                data=serialized_data,
            )

            # Persistir en SQLite
            res_id = self.db_manager.insert_capability_result(
                stage_name=stage_name,
                manager_name=manager_name,
                success=True,
                summary=summary,
                data=json.dumps(serialized_data) if serialized_data is not None else None,
            )
            result_obj.id = res_id

            return result_obj

        except Exception as e:
            error_summary = f"Error ejecutando binding de '{stage_name}' con manager '{manager_name}': {str(e)}"
            result_obj = CapabilityBindingResult(
                stage_name=stage_name,
                manager_name=manager_name,
                success=False,
                summary=error_summary,
                data={"error": str(e)},
            )
            res_id = self.db_manager.insert_capability_result(
                stage_name=stage_name,
                manager_name=manager_name,
                success=False,
                summary=error_summary,
                data=json.dumps({"error": str(e)}),
            )
            result_obj.id = res_id
            return result_obj
