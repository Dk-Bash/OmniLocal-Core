from datetime import datetime
from typing import Optional, List
from memory_priority.manager import MemoryPriorityManager
from maintenance_intelligence.manager import MaintenanceIntelligenceManager
from .models import StrategyRecommendation


class MaintenanceStrategyManager:
    """
    Capa de Optimización de Estrategia de Mantenimiento para OmniLocal-Core (Módulo 26).
    Analiza prioridades, riesgos, resultados históricos e impacto esperado para
    generar recomendaciones estratégicas.
    NO ejecuta acciones, NO modifica datos, NO elimina información.
    """

    def __init__(
        self,
        priority_manager: Optional[MemoryPriorityManager] = None,
        intelligence_manager: Optional[MaintenanceIntelligenceManager] = None,
    ):
        self.priority_manager = priority_manager or MemoryPriorityManager()
        self.intelligence_manager = intelligence_manager or MaintenanceIntelligenceManager()

    def generate_strategy(self) -> List[StrategyRecommendation]:
        """
        Obtiene tareas priorizadas e historial de inteligencia para calcular
        la recomendación estratégica de cada tarea.
        """
        priority_report = self.priority_manager.prioritize()
        intel_report = self.intelligence_manager.generate_report()

        recommendations: List[StrategyRecommendation] = []

        for task in priority_report.tasks:
            level = (task.priority_level or "low").lower()
            task_type = task.task_type

            if level == "critical":
                recommended_priority = "immediate"
                expected_benefit = 1.0
                reason = (
                    f"Tarea crítica '{task_type}' requiere ejecución inmediata para evitar fallos graves "
                    f"(Promedio histórico de score: {intel_report.average_score})."
                )
            elif level == "high":
                recommended_priority = "soon"
                expected_benefit = 0.8
                reason = (
                    f"Tarea de alta prioridad '{task_type}' recomendada para ejecución a corto plazo "
                    f"para reducir riesgo acumulado."
                )
            elif level == "medium":
                recommended_priority = "planned"
                expected_benefit = 0.5
                reason = (
                    f"Tarea de prioridad media '{task_type}' asignada a mantenimiento programado de rutina."
                )
            else:
                recommended_priority = "deferred"
                expected_benefit = 0.2
                reason = (
                    f"Tarea de baja prioridad '{task_type}' diferida temporalmente hasta atender tareas urgentes."
                )

            recommendations.append(
                StrategyRecommendation(
                    id=task.id,
                    task_type=task_type,
                    recommended_priority=recommended_priority,
                    reason=reason,
                    expected_benefit=expected_benefit,
                    created_at=datetime.now(),
                )
            )

        return recommendations
