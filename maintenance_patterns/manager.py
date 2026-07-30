from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_knowledge.manager import MaintenanceKnowledgeManager
from maintenance_patterns.models import MaintenancePattern


class MaintenancePatternManager:
    """Módulo 38: Capa de reconocimiento de patrones de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        knowledge_manager: Optional[MaintenanceKnowledgeManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.knowledge_manager = (
            knowledge_manager or MaintenanceKnowledgeManager(db_manager=self.db_manager)
        )

    def detect_patterns(self) -> List[MaintenancePattern]:
        """Detecta patrones a partir del conocimiento histórico de mantenimiento."""
        knowledge_entries = self.knowledge_manager.get_all_knowledge()

        if not knowledge_entries:
            k_obj = self.knowledge_manager.extract_knowledge()
            knowledge_entries = [self.db_manager.get_knowledge(k_obj.id)]

        success_count = sum(1 for k in knowledge_entries if k.get("knowledge_type") == "success_pattern")
        failure_count = sum(1 for k in knowledge_entries if k.get("knowledge_type") == "failure_pattern")
        hint_count = sum(1 for k in knowledge_entries if k.get("knowledge_type") == "improvement_hint")

        detected = []

        # Reglas Módulo 38:
        # Múltiples success_pattern -> frequent_success
        if success_count > 0:
            confidence = min(0.7 + (success_count * 0.1), 0.99)
            p_id = self.db_manager.insert_pattern(
                pattern_type="frequent_success",
                occurrences=success_count,
                confidence=confidence,
                description=f"Patrón de éxito frecuente: {success_count} registros de éxito identificados.",
            )
            detected.append(
                MaintenancePattern(
                    id=p_id,
                    pattern_type="frequent_success",
                    occurrences=success_count,
                    confidence=confidence,
                    description=f"Patrón de éxito frecuente: {success_count} registros de éxito identificados.",
                )
            )

        # Múltiples failure_pattern -> frequent_failure
        if failure_count > 0:
            confidence = min(0.75 + (failure_count * 0.1), 0.99)
            p_id = self.db_manager.insert_pattern(
                pattern_type="frequent_failure",
                occurrences=failure_count,
                confidence=confidence,
                description=f"Patrón de fallo frecuente: {failure_count} registros de fallo identificados.",
            )
            detected.append(
                MaintenancePattern(
                    id=p_id,
                    pattern_type="frequent_failure",
                    occurrences=failure_count,
                    confidence=confidence,
                    description=f"Patrón de fallo frecuente: {failure_count} registros de fallo identificados.",
                )
            )

        # Múltiples improvement_hint / recurring -> recurring_issue
        if hint_count > 0:
            p_id = self.db_manager.insert_pattern(
                pattern_type="recurring_issue",
                occurrences=hint_count,
                confidence=0.6,
                description=f"Incidencia recurrente: {hint_count} observaciones de mejora identificadas.",
            )
            detected.append(
                MaintenancePattern(
                    id=p_id,
                    pattern_type="recurring_issue",
                    occurrences=hint_count,
                    confidence=0.6,
                    description=f"Incidencia recurrente: {hint_count} observaciones de mejora identificadas.",
                )
            )

        return detected

    def detect_pattern(
        self,
        pattern_type: str = "frequent_success",
        occurrences: int = 1,
        confidence: float = 0.85,
        description: str = "Patrón registrado explícitamente.",
    ) -> MaintenancePattern:
        """Registra explícitamente un patrón de mantenimiento."""
        p_id = self.db_manager.insert_pattern(
            pattern_type=pattern_type,
            occurrences=occurrences,
            confidence=confidence,
            description=description,
        )
        return MaintenancePattern(
            id=p_id,
            pattern_type=pattern_type,
            occurrences=occurrences,
            confidence=confidence,
            description=description,
        )

    def get_pattern(self, pattern_id: int) -> Optional[dict]:
        """Obtiene un patrón por ID."""
        return self.db_manager.get_pattern(pattern_id)

    def get_patterns(self) -> List[dict]:
        """Obtiene la lista de patrones detectados."""
        return self.db_manager.get_patterns()
