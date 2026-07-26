from typing import Optional, List
from memory_integrity.manager import MemoryIntegrityManager
from memory_maintenance.models import MaintenanceRecommendation


class MaintenanceManager:
    """Capa de recomendación de mantenimiento de memoria para OmniLocal-Core (Módulo 18)."""

    def __init__(self, integrity_manager: Optional[MemoryIntegrityManager] = None):
        self.integrity_manager = integrity_manager or MemoryIntegrityManager()

    def generate_recommendations(self) -> List[MaintenanceRecommendation]:
        """Audita la memoria a través de MemoryIntegrityManager y genera recomendaciones con prioridades."""
        report = self.integrity_manager.audit_memory()
        recommendations: List[MaintenanceRecommendation] = []

        rec_counter = 1
        for issue in report.issues:
            issue_type = issue.issue_type

            if issue_type == "empty_content":
                recommendations.append(
                    MaintenanceRecommendation(
                        id=rec_counter,
                        issue_type=issue_type,
                        recommendation="Revisar memoria sin contenido",
                        priority="high"
                    )
                )
            elif issue_type == "duplicate_content":
                recommendations.append(
                    MaintenanceRecommendation(
                        id=rec_counter,
                        issue_type=issue_type,
                        recommendation="Considerar fusionar memorias duplicadas",
                        priority="medium"
                    )
                )
            elif issue_type == "invalid_importance":
                recommendations.append(
                    MaintenanceRecommendation(
                        id=rec_counter,
                        issue_type=issue_type,
                        recommendation="Corregir nivel de importancia",
                        priority="high"
                    )
                )
            else:
                recommendations.append(
                    MaintenanceRecommendation(
                        id=rec_counter,
                        issue_type=issue_type,
                        recommendation=f"Revisar problema de integridad ({issue_type})",
                        priority="medium"
                    )
                )
            rec_counter += 1

        return recommendations
