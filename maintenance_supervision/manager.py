from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_alert.manager import MaintenanceAlertManager
from maintenance_supervision.models import SupervisorDecision


class MaintenanceSupervisorManager:
    """Módulo 48: Capa Superior de Supervisión Lógica de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        alert_manager: Optional[MaintenanceAlertManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.alert_manager = (
            alert_manager or MaintenanceAlertManager(db_manager=self.db_manager)
        )

    def generate_supervisor_decision(
        self,
        alert_id: Optional[int] = None,
    ) -> List[SupervisorDecision]:
        """
        Genera recomendaciones de supervisión de alto nivel basadas en las alertas activas.
        Mantiene estrictamente observabilidad de solo lectura sin ejecutar mantenimiento ni alterar datos históricos.
        """
        alerts_to_process = []

        if alert_id is not None:
            al = self.db_manager.get_alert(alert_id)
            if al:
                alerts_to_process.append(al)
        else:
            alerts = self.db_manager.get_alerts()
            if not alerts:
                # Si no hay alertas registradas, evaluar alertas desde alert_manager
                generated_alerts = self.alert_manager.generate_alerts()
                alerts = [
                    self.db_manager.get_alert(a.id) for a in generated_alerts if a.id
                ]
            alerts_to_process.extend(alerts)

        decisions: List[SupervisorDecision] = []

        for al in alerts_to_process:
            if not al:
                continue
            a_id = al["id"]
            alert_type = al.get("alert_type", "information")
            rec_action = al.get("recommended_action", "Continuar supervisión.")

            if alert_type == "information":
                decision_type = "continue"
                priority = "low"
                reasoning = (
                    f"Decisión Supervisora: La alerta #{a_id} es estrictamente informativa sin riesgos. "
                    f"Se aprueba mantener el curso normal de ejecución."
                )
            elif alert_type == "warning":
                decision_type = "review"
                priority = "medium"
                reasoning = (
                    f"Decisión Supervisora: La alerta #{a_id} requiere revisión intermedia antes de proceder. "
                    f"Se recomienda auditar los tiempos y recursos asignados."
                )
            elif alert_type == "failure":
                decision_type = "stop"
                priority = "critical"
                reasoning = (
                    f"Decisión Supervisora: La alerta #{a_id} indica un fallo grave de ejecución. "
                    f"Se dicta la suspensión inmediata del proceso para prevenir inconsistencias en el sistema."
                )
            else:
                decision_type = "continue"
                priority = "low"
                reasoning = f"Decisión Supervisora: Alerta #{a_id} de tipo neutro."

            d_id = self.db_manager.insert_supervisor_decision(
                alert_id=a_id,
                decision_type=decision_type,
                recommended_action=rec_action,
                priority=priority,
                reasoning=reasoning,
            )

            decisions.append(
                SupervisorDecision(
                    id=d_id,
                    alert_id=a_id,
                    decision_type=decision_type,
                    recommended_action=rec_action,
                    priority=priority,
                    reasoning=reasoning,
                )
            )

        return decisions

    def get_supervisor_decision(self, decision_id: int) -> Optional[dict]:
        """Obtiene una decisión de supervisión por ID."""
        return self.db_manager.get_supervisor_decision(decision_id)

    def get_supervisor_decisions(self) -> List[dict]:
        """Obtiene todas las decisiones de supervisión."""
        return self.db_manager.get_supervisor_decisions()
