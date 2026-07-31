from typing import List, Dict, Any, Callable, Optional
from omnilocal_runtime.context import RuntimeContext
from omnilocal_runtime.models import RuntimeResult


ALLOWED_STAGE_STATUSES = {"pending", "running", "completed", "failed", "skipped"}


class RuntimePipeline:
    """Define y ejecuta una secuencia controlada de etapas para el Runtime de OmniLocal."""

    def __init__(self, name: str = "default_pipeline"):
        self.name = name
        self.stages: List[Dict[str, Any]] = []

    def add_stage(self, name: str, handler: Optional[Callable] = None) -> "RuntimePipeline":
        """Añade una etapa al pipeline."""
        stage = {
            "name": name,
            "status": "pending",
            "handler": handler,
        }
        self.stages.append(stage)
        return self

    def get_status(self) -> List[Dict[str, str]]:
        """Devuelve una lista con el estado actual de cada etapa."""
        return [
            {"name": stage["name"], "status": stage["status"]}
            for stage in self.stages
        ]

    def execute(
        self,
        context: RuntimeContext,
        db_manager: Optional[Any] = None,
        **kwargs
    ) -> RuntimeResult:
        """
        Ejecuta secuencialmente las etapas definidas en el pipeline.
        Mantiene actualizado el contexto de ejecución y persiste los cambios.
        """
        context.status = "running"
        if db_manager and context.id:
            db_manager.update_runtime_status(context.id, context.status, context.current_stage)

        errors: List[str] = []
        executed_stage_names: List[str] = []

        for stage in self.stages:
            stage_name = stage["name"]
            context.current_stage = stage_name
            stage["status"] = "running"

            if db_manager and context.id:
                db_manager.update_runtime_status(context.id, context.status, context.current_stage)

            try:
                if stage["handler"]:
                    stage["handler"](context, **kwargs)
                stage["status"] = "completed"
                executed_stage_names.append(stage_name)
            except Exception as e:
                stage["status"] = "failed"
                error_msg = f"Error in stage '{stage_name}': {str(e)}"
                errors.append(error_msg)
                context.status = "failed"

                if db_manager and context.id:
                    db_manager.update_runtime_status(context.id, context.status, context.current_stage)

                # Marcar etapas restantes como skipped
                for remaining in self.stages[self.stages.index(stage) + 1:]:
                    remaining["status"] = "skipped"

                break

        if not errors:
            context.status = "completed"
            if db_manager and context.id:
                db_manager.update_runtime_status(context.id, context.status, context.current_stage)
            success = True
            summary = (
                f"Pipeline '{self.name}' completado con éxito. "
                f"Etapas ejecutadas ({len(executed_stage_names)}/{len(self.stages)}): {', '.join(executed_stage_names)}."
            )
        else:
            success = False
            summary = f"Pipeline '{self.name}' falló en la etapa '{context.current_stage}'."

        return RuntimeResult(
            context_id=context.id or 0,
            success=success,
            summary=summary,
            executed_stages=self.get_status(),
            errors=errors,
        )
