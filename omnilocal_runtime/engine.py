from typing import Optional, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.context import RuntimeContext
from omnilocal_runtime.models import RuntimeResult
from omnilocal_runtime.pipeline import RuntimePipeline


class OmniLocalEngine:
    """Motor central Runtime para coordinar pipelines y administrar el contexto de ejecución."""

    def __init__(
        self,
        memory_manager: Optional[Any] = None,
        decision_manager: Optional[Any] = None,
        execution_manager: Optional[Any] = None,
        db_manager: Optional[SQLiteManager] = None,
        **kwargs
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.memory_manager = memory_manager
        self.decision_manager = decision_manager
        self.execution_manager = execution_manager
        self.extra_managers = kwargs

    def create_context(
        self,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RuntimeContext:
        """Crea y persiste un nuevo contexto de ejecución."""
        meta = metadata or {}
        status = "initialized"
        current_stage = "init"

        ctx_id = self.db_manager.insert_runtime_context(
            operation_type=operation_type,
            status=status,
            current_stage=current_stage,
        )

        return RuntimeContext(
            id=ctx_id,
            operation_type=operation_type,
            current_stage=current_stage,
            status=status,
            metadata=meta,
        )

    def _build_default_memory_optimization_pipeline(self) -> RuntimePipeline:
        """
        Construye el primer pipeline oficial: Memory Optimization Pipeline.
        Define las 8 etapas conceptuales sin ejecutar acciones destructivas reales.
        """
        pipeline = RuntimePipeline(name="memory_optimization_pipeline")

        stages = [
            "memory_analysis",
            "priority_evaluation",
            "simulation",
            "governance_check",
            "decision",
            "execution_planning",
            "result_tracking",
            "learning_feedback",
        ]

        for stage_name in stages:
            pipeline.add_stage(stage_name)

        return pipeline

    def run_pipeline(
        self,
        context: RuntimeContext,
        pipeline: Optional[RuntimePipeline] = None,
    ) -> RuntimeResult:
        """
        Ejecuta un pipeline dado o el pipeline predeterminado de optimización de memoria.
        Actualiza el estado en el contexto y persiste la trazabilidad.
        """
        target_pipeline = pipeline or self._build_default_memory_optimization_pipeline()
        result = target_pipeline.execute(context, db_manager=self.db_manager)
        return result

    def get_context(self, context_id: int) -> Optional[dict]:
        """Obtiene un contexto registrado por ID."""
        return self.db_manager.get_runtime_context(context_id)

    def get_contexts(self) -> list:
        """Obtiene todos los contextos registrados."""
        return self.db_manager.get_runtime_contexts()
