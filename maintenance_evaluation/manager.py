from datetime import datetime
from typing import Optional, List
from maintenance_audit.manager import AuditManager
from database.sqlite_manager import SQLiteManager
from .models import OutcomeEvaluation


class OutcomeEvaluationManager:
    """
    Capa de evaluación de resultados de mantenimiento (Módulo 24).
    Analiza eventos de auditoría registrados y evalúa su impacto/resultado.
    NO ejecuta cambios, NO modifica memorias y NO elimina información.
    """

    def __init__(
        self,
        audit_manager: Optional[AuditManager] = None,
        db_manager: Optional[SQLiteManager] = None,
    ):
        if audit_manager:
            self.audit_manager = audit_manager
            self.db_manager = self.audit_manager.db_manager
        elif db_manager:
            self.db_manager = db_manager
            self.audit_manager = AuditManager(db_manager=db_manager)
        else:
            self.audit_manager = AuditManager()
            self.db_manager = self.audit_manager.db_manager

    def evaluate_event(self, event_id: int) -> OutcomeEvaluation:
        """
        Obtiene el evento auditado, evalúa su resultado según su 'status',
        almacena y retorna la OutcomeEvaluation resultante.
        """
        event = self.audit_manager.get_event_by_id(event_id)
        if not event:
            raise ValueError(f"Audit event with ID {event_id} not found.")

        status = event.status.lower() if event.status else "unknown"

        if status == "completed":
            result_type = "positive"
            score = 0.9
            summary = "Simulation or maintenance event outcome was favorable"
        elif status == "blocked":
            result_type = "neutral"
            score = 0.5
            summary = "Maintenance event was blocked requiring prior approval"
        elif status == "failed":
            result_type = "negative"
            score = 0.1
            summary = "Maintenance event execution failed"
        else:
            result_type = "neutral"
            score = 0.5
            summary = f"Event status '{event.status}' evaluated"

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        eval_id = self.db_manager.insert_outcome_evaluation(
            event_id=event_id,
            result_type=result_type,
            score=score,
            summary=summary,
            created_at=now_str,
        )

        return OutcomeEvaluation(
            id=eval_id,
            event_id=event_id,
            result_type=result_type,
            score=score,
            summary=summary,
            created_at=now,
        )

    def get_evaluations_for_event(self, event_id: int) -> List[OutcomeEvaluation]:
        """
        Obtiene todas las evaluaciones asociadas a un evento específico.
        """
        rows = self.db_manager.get_outcomes_by_event(event_id)
        evaluations: List[OutcomeEvaluation] = []
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

            evaluations.append(
                OutcomeEvaluation(
                    id=row["id"],
                    event_id=row["event_id"],
                    result_type=row["result_type"],
                    score=float(row["score"]),
                    summary=row["summary"],
                    created_at=dt,
                )
            )
        return evaluations
