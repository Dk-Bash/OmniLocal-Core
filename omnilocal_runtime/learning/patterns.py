from typing import List, Dict, Any, Optional
from collections import Counter


class RuntimePatternAnalyzer:
    """
    Capa de Análisis de Patrones para Aprendizaje Runtime (Runtime Block 08).
    Analiza datos históricos de RuntimeValidationReport, RuntimePerformanceReport, RuntimeDecisionReport o ciclos autónomos.
    """

    @staticmethod
    def detect_failure_patterns(historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analiza registros históricos para detectar patrones de fallo reincidentes.
        """
        stage_counter = Counter()

        for item in historical_data:
            # Caso 1: ciclo autónomo con detalles de etapa
            if "details" in item and isinstance(item["details"], list):
                for detail in item["details"]:
                    if detail.get("status") == "failed":
                        st_name = detail.get("stage_name", "unknown")
                        stage_counter[st_name] += 1

            # Caso 2: reporte de validación con most_failed_stage o failed_stages > 0
            most_failed = item.get("most_failed_stage")
            if most_failed and most_failed != "none":
                stage_counter[most_failed] += 1

            # Caso 3: estado directo 'failed' o 'partial'
            if item.get("status") in ["failed", "partial"]:
                stage_name = item.get("failed_stage") or item.get("scenario_name") or "general_execution"
                stage_counter[stage_name] += 1

        patterns = []
        for stage_name, count in stage_counter.items():
            patterns.append({
                "pattern_type": "failure_pattern",
                "target_area": stage_name,
                "occurrences": count,
                "description": f"Se detectaron {count} fallos en el área/etapa '{stage_name}'."
            })

        return patterns

    @staticmethod
    def detect_success_patterns(historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analiza registros históricos para detectar patrones de éxito y estabilidad.
        """
        total = len(historical_data)
        if total == 0:
            return []

        successful_count = sum(
            1 for item in historical_data
            if item.get("status") in ["passed", "completed", "success"]
        )

        patterns = []
        if successful_count > 0:
            rate = round((successful_count / total) * 100.0, 2)
            patterns.append({
                "pattern_type": "success_pattern",
                "target_area": "overall_runtime",
                "successful_executions": successful_count,
                "total_executions": total,
                "success_rate": rate,
                "description": f"Tasa de éxito general del {rate}% con {successful_count} ejecuciones exitosas de {total}."
            })

        return patterns

    @staticmethod
    def compare_executions(execution_a: Dict[str, Any], execution_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara dos ejecuciones y resalta diferencias de estado y tiempo.
        """
        time_a = execution_a.get("execution_time", execution_a.get("average_execution_time", 0.0))
        time_b = execution_b.get("execution_time", execution_b.get("average_execution_time", 0.0))

        status_a = execution_a.get("status", "unknown")
        status_b = execution_b.get("status", "unknown")

        time_diff = round(time_b - time_a, 4)

        return {
            "status_a": status_a,
            "status_b": status_b,
            "time_a": time_a,
            "time_b": time_b,
            "time_difference_sec": time_diff,
            "status_changed": status_a != status_b,
            "performance_improved": time_diff < 0
        }

    @staticmethod
    def identify_improvement_area(performance_reports: List[Dict[str, Any]], validation_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identifica el área prioritaria de mejora analizando reportes de rendimiento y de validación.
        """
        failed_patterns = RuntimePatternAnalyzer.detect_failure_patterns(validation_reports)
        if failed_patterns:
            sorted_failures = sorted(failed_patterns, key=lambda x: x["occurrences"], reverse=True)
            top_failure = sorted_failures[0]
            return {
                "target_area": top_failure["target_area"],
                "reason": f"Se detectó un patrón recurrente de fallos en {top_failure['target_area']} ({top_failure['occurrences']} incidencias).",
                "priority": "high" if top_failure["occurrences"] > 2 else "medium"
            }

        if performance_reports:
            latest = performance_reports[0]
            s_rate = latest.get("success_rate", 100.0)
            most_failed = latest.get("most_failed_stage", "none")

            if most_failed != "none":
                return {
                    "target_area": most_failed,
                    "reason": f"Reporte de rendimiento identifica la etapa '{most_failed}' como la más problemática.",
                    "priority": "medium"
                }

            if s_rate < 90.0:
                return {
                    "target_area": "runtime_reliability",
                    "reason": f"La tasa de éxito es del {s_rate}%, inferior al objetivo del 90%.",
                    "priority": "medium"
                }

        return {
            "target_area": "optimization",
            "reason": "El sistema presenta estabilidad alta; se sugiere optimización de tiempos y recursos.",
            "priority": "low"
        }
