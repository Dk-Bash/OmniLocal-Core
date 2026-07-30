from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_monitoring.manager import MaintenanceMonitoringManager
from maintenance_alert.models import MaintenanceAlert


class MaintenanceAlertManager:
    """Módulo 47: Capa de Generación de Alertas Inteligentes de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        monitoring_manager: Optional[MaintenanceMonitoringManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.monitoring_manager = (
            monitoring_manager or MaintenanceMonitoringManager(db_manager=self.db_manager)
        )

    def generate_alerts(
        self,
        monitoring_id: Optional[int] = None,
    ) -> List[MaintenanceAlert]:
        """
        Genera alertas inteligentes a partir de informes de monitoreo supervisados.
        No ejecuta mantenimiento ni modifica resultados históricos.
        """
        reports_to_process = []

        if monitoring_id is not None:
            rep = self.db_manager.get_monitoring_report(monitoring_id)
            if rep:
                reports_to_process.append(rep)
        else:
            reports = self.db_manager.get_monitoring_reports()
            if not reports:
                # Si no existen informes, evaluar un nuevo monitoreo
                m_reports = self.monitoring_manager.generate_monitoring_report()
                reports = [
                    self.db_manager.get_monitoring_report(r.id) for r in m_reports if r.id
                ]
            reports_to_process.extend(reports)

        alerts: List[MaintenanceAlert] = []

        for rep in reports_to_process:
            if not rep:
                continue
            m_id = rep["id"]
            health_status = rep.get("health_status", "healthy")

            if health_status == "healthy":
                alert_type = "information"
                severity = "low"
                message = f"Informativa: El ciclo de mantenimiento #{m_id} opera en estado saludable."
                recommended_action = "Continuar supervisión autónoma estándar sin cambios."
            elif health_status == "warning":
                alert_type = "warning"
                severity = "medium"
                message = f"Advertencia: El ciclo de mantenimiento #{m_id} presenta posibles demoras o advertencias de ejecución."
                recommended_action = "Revisar logs de monitoreo y evaluar progresos de ejecución."
            elif health_status == "critical":
                alert_type = "failure"
                severity = "critical"
                message = f"Fallo Crítico: El ciclo de mantenimiento #{m_id} reporta una falla grave de ejecución."
                recommended_action = "Detener inmediatamente el flujo y solicitar intervención manual."
            else:
                alert_type = "information"
                severity = "low"
                message = f"Informativa: Estado de monitoreo #{m_id} neutro."
                recommended_action = "Mantener observación."

            a_id = self.db_manager.insert_alert(
                monitoring_id=m_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                recommended_action=recommended_action,
            )

            alerts.append(
                MaintenanceAlert(
                    id=a_id,
                    monitoring_id=m_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    recommended_action=recommended_action,
                )
            )

        return alerts

    def get_alert(self, alert_id: int) -> Optional[dict]:
        """Obtiene una alerta por ID."""
        return self.db_manager.get_alert(alert_id)

    def get_alerts(self) -> List[dict]:
        """Obtiene todas las alertas generadas."""
        return self.db_manager.get_alerts()
