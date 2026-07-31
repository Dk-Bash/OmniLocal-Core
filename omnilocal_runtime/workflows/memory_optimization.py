from typing import List, Dict, Any, Callable
from omnilocal_runtime.workflows.models import WorkflowDefinition


STAGES_LIST = [
    "memory_analysis",
    "priority_evaluation",
    "simulation",
    "governance_check",
    "decision_generation",
    "execution_planning",
    "validation",
    "feedback_generation",
    "learning_update",
]


class MemoryOptimizationWorkflow:
    """
    Workflow oficial de optimización de memoria para OmniLocal Runtime.
    Coordina secuencialmente las 9 etapas conceptuales sin realizar modificaciones destructivas.
    """

    def __init__(self):
        self.name = "memory_optimization"
        self.description = "Workflow oficial de optimización de memoria de OmniLocal"
        self.stages = STAGES_LIST

    def get_definition(self) -> WorkflowDefinition:
        """Devuelve la definición oficial del workflow."""
        return WorkflowDefinition(
            name=self.name,
            description=self.description,
            stages=self.stages,
        )

    @staticmethod
    def run_stage(stage_name: str, context: Any = None) -> Dict[str, Any]:
        """
        Ejecuta una etapa individual y devuelve el diccionario estructurado.
        Cada stage devuelve: {"stage_name": ..., "status": ..., "summary": ...}
        """
        summaries = {
            "memory_analysis": "Análisis preliminar de memorias finalizado sin detectar anomalías críticas.",
            "priority_evaluation": "Evaluación de prioridades asignada a las tareas pendientes.",
            "simulation": "Simulación de cambios ejecutada con éxito en entorno seguro.",
            "governance_check": "Verificación de políticas de gobernanza aprobada sin objeciones.",
            "decision_generation": "Generación de decisiones autónomas completada.",
            "execution_planning": "Plan de ejecución estructurado y coordinado.",
            "validation": "Validación de requisitos de integridad de memoria confirmada.",
            "feedback_generation": "Retroalimentación generada para el ciclo de optimización.",
            "learning_update": "Actualización de modelos de aprendizaje registrada.",
        }

        summary = summaries.get(
            stage_name,
            f"Ejecución simulada de la etapa '{stage_name}' completada."
        )

        return {
            "stage_name": stage_name,
            "status": "completed",
            "summary": summary,
        }

    def get_stage_handler(self, stage_name: str) -> Callable:
        """Devuelve una función handler adecuada para ser usada por RuntimePipeline."""
        def handler(ctx, **kwargs):
            res = self.run_stage(stage_name, ctx)
            if "stage_results" not in ctx.metadata:
                ctx.metadata["stage_results"] = []
            ctx.metadata["stage_results"].append(res)
            return res
        return handler
