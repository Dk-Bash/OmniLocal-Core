from typing import List, Dict, Any, Optional
from collections import Counter


class RuntimeAnalytics:
    """
    Capa de Análisis de Observabilidad Runtime (Runtime Block 06).
    Proporciona funciones puras para calcular tasas de éxito, tiempos promedio y detectar etapas con fallos.
    """

    @staticmethod
    def calculate_success_rate(total_executions: int, successful_executions: int) -> float:
        """
        Calcula el porcentaje de éxito (0.0 - 100.0).
        """
        if total_executions <= 0:
            return 0.0
        return round((successful_executions / total_executions) * 100.0, 2)

    @staticmethod
    def calculate_average_execution_time(execution_times: List[float]) -> float:
        """
        Calcula el tiempo promedio de ejecución en segundos.
        """
        if not execution_times:
            return 0.0
        return round(sum(execution_times) / len(execution_times), 4)

    @staticmethod
    def identify_failed_stages(details_or_reports: List[Dict[str, Any]]) -> str:
        """
        Analiza una lista de registros de etapas o ejecuciones para identificar la etapa que falla más frecuentemente.
        """
        failed_counter = Counter()

        for item in details_or_reports:
            # Caso 1: detalle de etapa en AutonomousExecutionCycle
            if isinstance(item, dict):
                stage_name = item.get("stage_name")
                status = item.get("status")
                if status == "failed" and stage_name:
                    failed_counter[stage_name] += 1

                # Caso 2: reportes de validación con summary o most_failed_stage
                failed_stage = item.get("most_failed_stage")
                if failed_stage and failed_stage != "none":
                    failed_counter[failed_stage] += 1

        if not failed_counter:
            return "none"

        most_common = failed_counter.most_common(1)
        return most_common[0][0] if most_common else "none"

    @staticmethod
    def generate_summary(
        total_executions: int,
        success_rate: float,
        avg_time: float,
        most_failed_stage: str
    ) -> str:
        """
        Genera un resumen textual del rendimiento del Runtime.
        """
        if total_executions == 0:
            return "No se han registrado ejecuciones en el Runtime."

        summary = (
            f"Analizadas {total_executions} ejecuciones del Runtime. "
            f"Tasa de éxito: {success_rate}%, Tiempo promedio de ejecución: {avg_time}s. "
        )
        if most_failed_stage != "none":
            summary += f"Etapa con mayor tasa de fallos: '{most_failed_stage}'."
        else:
            summary += "No se detectaron etapas críticas con fallos reincidentes."

        return summary
