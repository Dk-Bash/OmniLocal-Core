from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_supervision.manager import MaintenanceSupervisorManager
from maintenance_governance.models import GovernanceEvaluation


class MaintenanceGovernanceManager:
    """Módulo 49: Capa de Evaluación de Gobernanza de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        supervisor_manager: Optional[MaintenanceSupervisorManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.supervisor_manager = (
            supervisor_manager or MaintenanceSupervisorManager(db_manager=self.db_manager)
        )

    def evaluate_governance(
        self,
        decision_id: Optional[int] = None,
    ) -> List[GovernanceEvaluation]:
        """
        Evalúa decisiones supervisadas contra políticas generales de gobernanza.
        Garantiza neutralidad y observabilidad sin modificar estados anteriores.
        """
        decisions_to_process = []

        if decision_id is not None:
            dec = self.db_manager.get_supervisor_decision(decision_id)
            if dec:
                decisions_to_process.append(dec)
        else:
            decisions = self.db_manager.get_supervisor_decisions()
            if not decisions:
                # Si no hay decisiones guardadas, generar vía supervisor_manager
                generated_decisions = self.supervisor_manager.generate_supervisor_decision()
                decisions = [
                    self.db_manager.get_supervisor_decision(d.id) for d in generated_decisions if d.id
                ]
            decisions_to_process.extend(decisions)

        evaluations: List[GovernanceEvaluation] = []

        for dec in decisions_to_process:
            if not dec:
                continue
            d_id = dec["id"]
            decision_type = dec.get("decision_type", "continue")

            if decision_type == "continue":
                governance_status = "approved"
                risk_level = "low"
                rules_checked = "Gobernanza Aprobada: [Regla 1: Alineación Estándar OK] [Regla 2: Límite de Riesgo Normal]."
                reasoning = (
                    f"Evaluación de Gobernanza: La decisión supervisada #{d_id} ('continue') "
                    f"cumple totalmente con las políticas de gobernanza operativas. Acción Aprobada."
                )
            elif decision_type == "review":
                governance_status = "review_required"
                risk_level = "medium"
                rules_checked = "Gobernanza Bajo Revisión: [Regla 1: Umbral de Incertidumbre Activo] [Regla 2: Auditoría Requerida]."
                reasoning = (
                    f"Evaluación de Gobernanza: La decisión supervisada #{d_id} ('review') "
                    f"requiere auditoría intermedia de gobernanza antes de proceder. Acción Detenida para Revisión."
                )
            elif decision_type == "stop":
                governance_status = "blocked"
                risk_level = "critical"
                rules_checked = "Gobernanza Bloqueada: [Regla 1: Violación Severa / Detención Solicitada] [Regla 2: Riesgo Crítico Detectado]."
                reasoning = (
                    f"Evaluación de Gobernanza: La decisión supervisada #{d_id} ('stop') "
                    f"ha violado los límites de riesgo aceptables. Acción Bloqueada Preventivamente."
                )
            else:
                governance_status = "approved"
                risk_level = "low"
                rules_checked = "Gobernanza General: Reglas estándar."
                reasoning = f"Evaluación de Gobernanza: Decisión #{d_id} procesada."

            eval_id = self.db_manager.insert_governance_evaluation(
                decision_id=d_id,
                governance_status=governance_status,
                risk_level=risk_level,
                rules_checked=rules_checked,
                reasoning=reasoning,
            )

            evaluations.append(
                GovernanceEvaluation(
                    id=eval_id,
                    decision_id=d_id,
                    governance_status=governance_status,
                    risk_level=risk_level,
                    rules_checked=rules_checked,
                    reasoning=reasoning,
                )
            )

        return evaluations

    def get_governance_evaluation(self, evaluation_id: int) -> Optional[dict]:
        """Obtiene una evaluación de gobernanza por ID."""
        return self.db_manager.get_governance_evaluation(evaluation_id)

    def get_governance_evaluations(self) -> List[dict]:
        """Obtiene todas las evaluaciones de gobernanza."""
        return self.db_manager.get_governance_evaluations()
