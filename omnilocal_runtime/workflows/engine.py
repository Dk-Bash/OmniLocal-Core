import json
from typing import Optional, Dict, Any, List, Union
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.engine import OmniLocalEngine
from omnilocal_runtime.pipeline import RuntimePipeline
from omnilocal_runtime.workflows.models import WorkflowDefinition, WorkflowExecution
from omnilocal_runtime.workflows.memory_optimization import MemoryOptimizationWorkflow


class WorkflowEngine:
    """
    Motor de ejecución de workflows de OmniLocal Runtime.
    Registra workflows y los ejecuta coordinándolos mediante OmniLocalEngine e inyección de dependencias.
    Soporta CapabilityBindingManager para conectar etapas con capacidades (managers) reales.
    """

    def __init__(
        self,
        engine: OmniLocalEngine,
        capability_binding_manager: Optional[Any] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        self.engine = engine
        self.capability_binding_manager = capability_binding_manager
        self.db_manager = db_manager or getattr(engine, "db_manager", SQLiteManager())
        self.registry: Dict[str, WorkflowDefinition] = {}

        # Auto-registrar el workflow por defecto de optimización de memoria
        mem_wf = MemoryOptimizationWorkflow()
        self.register_workflow(mem_wf.get_definition())

    def register_workflow(
        self,
        workflow: Union[WorkflowDefinition, Any]
    ) -> WorkflowDefinition:
        """Registra un workflow en el motor."""
        if hasattr(workflow, "get_definition"):
            wf_def = workflow.get_definition()
        else:
            wf_def = workflow

        if not isinstance(wf_def, WorkflowDefinition):
            raise TypeError("workflow must be a WorkflowDefinition instance or provide get_definition()")

        self.registry[wf_def.name] = wf_def
        return wf_def

    def execute_workflow(
        self,
        workflow_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """
        Ejecuta un workflow registrado generando un contexto y un pipeline en OmniLocalEngine.
        Registra cada etapa con su {"stage_name": ..., "status": ..., "summary": ...} y persiste el resultado.
        """
        if workflow_name not in self.registry:
            raise ValueError(f"Workflow '{workflow_name}' is not registered.")

        wf_def = self.registry[workflow_name]
        meta = metadata or {}

        # 1. Crear contexto en OmniLocalEngine
        context = self.engine.create_context(
            operation_type=f"workflow:{workflow_name}",
            metadata=meta,
        )

        # 2. Insertar inicio de WorkflowExecution en SQLite
        exec_id = self.db_manager.insert_workflow_execution(
            workflow_id=workflow_name,
            context_id=context.id or 0,
            status="running",
            current_stage="init",
            results=json.dumps([]),
        )

        execution = WorkflowExecution(
            id=exec_id,
            workflow_id=workflow_name,
            context_id=context.id or 0,
            status="running",
            current_stage="init",
            results=[],
        )

        # 3. Construir RuntimePipeline
        pipeline = RuntimePipeline(name=f"workflow_pipeline:{workflow_name}")
        mem_workflow_helper = MemoryOptimizationWorkflow()

        for stage in wf_def.stages:
            stage_name = stage if isinstance(stage, str) else stage.get("name", "unknown_stage")

            if self.capability_binding_manager and self.capability_binding_manager.get_binding(stage_name):
                def make_binding_handler(s_name):
                    def handler(ctx):
                        binding_res = self.capability_binding_manager.execute_binding(s_name, ctx)
                        res = {
                            "stage_name": binding_res.stage_name,
                            "status": "completed" if binding_res.success else "failed",
                            "summary": binding_res.summary,
                            "manager_name": binding_res.manager_name,
                            "data": binding_res.data,
                        }
                        if "stage_results" not in ctx.metadata:
                            ctx.metadata["stage_results"] = []
                        ctx.metadata["stage_results"].append(res)
                        return res
                    return handler
                handler = make_binding_handler(stage_name)
            elif workflow_name == "memory_optimization":
                handler = mem_workflow_helper.get_stage_handler(stage_name)
            else:
                def make_generic_handler(s_name):
                    def handler(ctx):
                        res = {
                            "stage_name": s_name,
                            "status": "completed",
                            "summary": f"Ejecución de la etapa '{s_name}' completada."
                        }
                        if "stage_results" not in ctx.metadata:
                            ctx.metadata["stage_results"] = []
                        ctx.metadata["stage_results"].append(res)
                        return res
                    return handler
                handler = make_generic_handler(stage_name)

            pipeline.add_stage(stage_name, handler)

        # 4. Ejecutar Pipeline vía OmniLocalEngine
        pipeline_result = self.engine.run_pipeline(context, pipeline)

        # 5. Obtener resultados detallados de cada etapa
        stage_results = context.metadata.get("stage_results", [])
        if not stage_results:
            # Fallback a los resultados de las etapas registradas por pipeline
            for s in pipeline_result.executed_stages:
                stage_results.append({
                    "stage_name": s["name"],
                    "status": s["status"],
                    "summary": f"Etapa '{s['name']}' estado: {s['status']}"
                })

        execution.status = context.status
        execution.current_stage = context.current_stage
        execution.results = stage_results

        # 6. Actualizar persistencia en DB
        self.db_manager.update_workflow_execution(
            execution_id=exec_id,
            status=execution.status,
            current_stage=execution.current_stage,
            results=json.dumps(stage_results),
        )

        return execution

    def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """Obtiene una ejecución de workflow persistida por ID."""
        row = self.db_manager.get_workflow_execution(execution_id)
        if not row:
            return None

        results_parsed = []
        if row.get("results"):
            try:
                results_parsed = json.loads(row["results"])
            except Exception:
                results_parsed = []

        return WorkflowExecution(
            id=row["id"],
            workflow_id=row["workflow_id"],
            context_id=row["context_id"],
            status=row["status"],
            current_stage=row["current_stage"],
            results=results_parsed,
            created_at=row.get("created_at"),
        )

    def get_executions(self) -> List[Dict[str, Any]]:
        """Devuelve todas las ejecuciones de workflow registradas."""
        return self.db_manager.get_workflow_executions()
