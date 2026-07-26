from typing import Optional, List
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from memory_integrity.models import MemoryIssue, IntegrityReport


class MemoryIntegrityManager:
    """Capa de auditoría e integridad de la memoria para OmniLocal-Core (Módulo 17)."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        db_manager: Optional[SQLiteManager] = None
    ):
        self.memory_manager = memory_manager
        if db_manager:
            self.db_manager = db_manager
        elif memory_manager and hasattr(memory_manager, 'db_manager'):
            self.db_manager = memory_manager.db_manager
        else:
            self.db_manager = SQLiteManager()

    def audit_memory(self) -> IntegrityReport:
        """Audita todas las memorias guardadas para detectar inconsistencias sin modificarlas."""
        memories = self.db_manager.get_all_memories_for_audit()
        total_checked = len(memories)
        issues: List[MemoryIssue] = []

        seen_contents = {}  # norm_content -> first memory_id seen

        for mem in memories:
            mem_id = mem.get("id")
            content = mem.get("content", "")
            importance = mem.get("importance", 0.0)

            # 1. Memorias vacías
            if not content or not str(content).strip():
                issues.append(
                    MemoryIssue(
                        memory_id=mem_id,
                        issue_type="empty_content",
                        description="Memory has empty content",
                        severity="medium"
                    )
                )

            # 2. Duplicados exactos
            norm_content = str(content).strip() if content else ""
            if norm_content:
                if norm_content in seen_contents:
                    first_id = seen_contents[norm_content]
                    issues.append(
                        MemoryIssue(
                            memory_id=mem_id,
                            issue_type="duplicate_content",
                            description=f"Duplicate content found in memory {mem_id} (identical to memory {first_id})",
                            severity="medium"
                        )
                    )
                else:
                    seen_contents[norm_content] = mem_id

            # 3. Importancia inválida (importance < 0.0 or importance > 1.0)
            if importance is not None and (importance < 0.0 or importance > 1.0):
                issues.append(
                    MemoryIssue(
                        memory_id=mem_id,
                        issue_type="invalid_importance",
                        description=f"Memory importance {importance} is out of bounds [0.0, 1.0]",
                        severity="high"
                    )
                )

        return IntegrityReport(
            total_checked=total_checked,
            issues_found=len(issues),
            issues=issues
        )
