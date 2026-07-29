from typing import List, Optional, Union
from database.sqlite_manager import SQLiteManager
from maintenance_approval.manager import ExecutionApprovalManager
from maintenance_approval.models import ExecutionApproval
from maintenance_tracking.models import ExecutionTracking


class ExecutionTrackingManager:
    """Módulo 34: Capa de seguimiento del ciclo de vida de ejecución de mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        approval_manager: Optional[ExecutionApprovalManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.approval_manager = (
            approval_manager or ExecutionApprovalManager(db_manager=self.db_manager)
        )

    def create_tracking(
        self,
        approval_id: Optional[int] = None,
        approval: Optional[ExecutionApproval] = None,
        message: str = "",
    ) -> ExecutionTracking:
        """Crea un registro de seguimiento basado en la aprobación formal."""
        target_approval = approval

        if target_approval is None and approval_id is not None:
            raw = self.db_manager.get_execution_approval(approval_id)
            if raw:
                target_approval = ExecutionApproval(
                    id=raw["id"],
                    plan_id=raw["plan_id"],
                    validation_id=raw["validation_id"],
                    approval_status=raw["approval_status"],
                    approved=raw["approved"],
                    reason=raw["reason"],
                    created_at=raw["created_at"],
                )

        if target_approval is None:
            target_approval = self.approval_manager.evaluate_approval(plan_id=1)

        app_id = target_approval.id if target_approval.id is not None else 0

        # Reglas de Negocio
        # Si approved=True -> status="pending", progress=0.0
        # Si approved=False -> status="cancelled", progress=0.0
        if target_approval.approved:
            status = "pending"
            progress = 0.0
            default_msg = message or "Seguimiento de ejecución iniciado en estado pendiente."
        else:
            status = "cancelled"
            progress = 0.0
            default_msg = message or "Seguimiento cancelado: el plan de ejecución no está aprobado formalmente."

        tracking_id = self.db_manager.insert_execution_tracking(
            approval_id=app_id,
            status=status,
            progress=progress,
            message=default_msg,
        )

        return ExecutionTracking(
            id=tracking_id,
            approval_id=app_id,
            status=status,
            progress=progress,
            message=default_msg,
        )

    def update_status(
        self,
        tracking_id: int,
        status: str,
        progress: float,
        message: str = "",
    ) -> ExecutionTracking:
        """Actualiza el estado y progreso de un seguimiento activo."""
        valid_statuses = {"pending", "running", "completed", "failed", "cancelled"}
        if status not in valid_statuses:
            raise ValueError(f"Estado '{status}' no es válido. Debe ser uno de {valid_statuses}.")

        if progress < 0.0 or progress > 1.0:
            raise ValueError("El progreso debe ser un valor entre 0.0 y 1.0 inclusive.")

        # Obtener registro actual
        raw = self.db_manager.get_execution_tracking(tracking_id)
        if not raw:
            raise ValueError(f"No existe registro de seguimiento con ID {tracking_id}.")

        msg = message if message else raw.get("message", "")

        self.db_manager.update_execution_tracking(
            tracking_id=tracking_id,
            status=status,
            progress=progress,
            message=msg,
        )

        updated_raw = self.db_manager.get_execution_tracking(tracking_id)
        if updated_raw:
            return ExecutionTracking(
                id=updated_raw["id"],
                approval_id=updated_raw["approval_id"],
                status=updated_raw["status"],
                progress=updated_raw["progress"],
                message=updated_raw["message"],
                created_at=updated_raw["created_at"],
                updated_at=updated_raw["updated_at"],
            )

        return ExecutionTracking(
            id=tracking_id,
            approval_id=raw["approval_id"],
            status=status,
            progress=progress,
            message=msg,
        )

    def get_tracking(self, tracking_id: int) -> Optional[dict]:
        """Obtiene un registro de seguimiento por ID."""
        return self.db_manager.get_execution_tracking(tracking_id)

    def get_trackings(self) -> List[dict]:
        """Obtiene el historial completo de seguimientos."""
        return self.db_manager.get_execution_trackings()
