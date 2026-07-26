from datetime import datetime
from typing import Optional, List
from database.sqlite_manager import SQLiteManager
from .models import AuditEvent


class AuditManager:
    """
    Capa de auditoría de historial de mantenimiento (Módulo 23).
    Registra eventos del sistema de mantenimiento sin ejecutar modificaciones
    en memorias, sesiones o conocimiento.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.db_manager.create_tables()

    def record_event(
        self, event_type: str, source_layer: str, description: str, status: str
    ) -> AuditEvent:
        """
        Registra un evento de auditoría de mantenimiento en SQLite.
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        event_id = self.db_manager.insert_audit_event(
            event_type=event_type,
            source_layer=source_layer,
            description=description,
            status=status,
            created_at=now_str,
        )

        return AuditEvent(
            id=event_id,
            event_type=event_type,
            source_layer=source_layer,
            description=description,
            status=status,
            created_at=now,
        )

    def get_history(self) -> List[AuditEvent]:
        """
        Devuelve el historial completo de eventos de auditoría ordenados cronológicamente.
        """
        rows = self.db_manager.get_all_audit_events()
        events: List[AuditEvent] = []
        for row in rows:
            created_at_val = row.get("created_at")
            if isinstance(created_at_val, str):
                try:
                    dt = datetime.fromisoformat(created_at_val.replace(" ", "T"))
                except ValueError:
                    dt = datetime.now()
            elif isinstance(created_at_val, datetime):
                dt = created_at_val
            else:
                dt = datetime.now()

            events.append(
                AuditEvent(
                    id=row["id"],
                    event_type=row["event_type"],
                    source_layer=row["source_layer"],
                    description=row["description"],
                    status=row["status"],
                    created_at=dt,
                )
            )
        return events
