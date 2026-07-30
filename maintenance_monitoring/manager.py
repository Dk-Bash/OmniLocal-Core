from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_workflow.manager import MaintenanceWorkflowManager
from maintenance_tracking.manager import ExecutionTrackingManager
from maintenance_monitoring.models import MaintenanceMonitoringReport


class MaintenanceMonitoringManager:
    """Módulo 46: Capa de Monitoreo del Estado Actual de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        workflow_manager: Optional[MaintenanceWorkflowManager] = None,
        tracking_manager: Optional[ExecutionTrackingManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.workflow_manager = (
            workflow_manager or MaintenanceWorkflowManager(db_manager=self.db_manager)
        )
        self.tracking_manager = (
            tracking_manager or ExecutionTrackingManager(db_manager=self.db_manager)
        )

    def generate_monitoring_report(
        self,
        workflow_id: Optional[int] = None,
        execution_status: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> List[MaintenanceMonitoringReport]:
        """
        Genera informes de monitoreo observando el estado actual de los flujos de mantenimiento.
        Capacidad estrictamente observadora/supervisora de solo lectura hacia los sistemas anteriores.
        """
        workflows_to_monitor = []

        if workflow_id is not None:
            wf = self.db_manager.get_workflow(workflow_id)
            if wf:
                workflows_to_monitor.append(wf)
            else:
                workflows_to_monitor.append({"id": workflow_id, "status": execution_status or "pending"})
        else:
            workflows = self.db_manager.get_workflows()
            if workflows:
                workflows_to_monitor.extend(workflows)
            else:
                # Si no hay workflows guardados, monitorear un workflow simulado si se especificaron parámetros
                if execution_status is not None:
                    workflows_to_monitor.append({"id": 1, "status": execution_status})

        results: List[MaintenanceMonitoringReport] = []

        for wf in workflows_to_monitor:
            wf_id = wf.get("id", 1)
            status = execution_status or wf.get("status", "pending")

            if status == "completed":
                health_status = "healthy"
                prog = 1.0 if progress is None else float(progress)
                obs = f"Monitoreo OK: El flujo #{wf_id} ha completado su ejecución satisfactoriamente."
            elif status == "running":
                health_status = "warning"
                prog = 0.5 if progress is None else float(progress)
                obs = f"Monitoreo Advertencia: El flujo #{wf_id} está actualmente en curso de ejecución."
            elif status == "failed":
                health_status = "critical"
                prog = 0.0 if progress is None else float(progress)
                obs = f"Monitoreo Crítico: El flujo #{wf_id} ha fallado durante la ejecución de mantenimiento."
            else:
                health_status = "warning"
                prog = 0.0 if progress is None else float(progress)
                obs = f"Monitoreo Pendiente: El flujo #{wf_id} se encuentra en estado '{status}'."

            # Garantizar rango
            prog = max(0.0, min(1.0, prog))

            rep_id = self.db_manager.insert_monitoring_report(
                workflow_id=wf_id,
                execution_status=status,
                health_status=health_status,
                progress=prog,
                observations=obs,
            )

            results.append(
                MaintenanceMonitoringReport(
                    id=rep_id,
                    workflow_id=wf_id,
                    execution_status=status,
                    health_status=health_status,
                    progress=prog,
                    observations=obs,
                )
            )

        return results

    def get_monitoring_report(self, report_id: int) -> Optional[dict]:
        """Obtiene un informe de monitoreo por ID."""
        return self.db_manager.get_monitoring_report(report_id)

    def get_monitoring_reports(self) -> List[dict]:
        """Obtiene todos los informes de monitoreo."""
        return self.db_manager.get_monitoring_reports()
