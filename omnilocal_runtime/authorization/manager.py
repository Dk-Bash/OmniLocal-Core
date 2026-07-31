import json
from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.plan_validation.manager import RuntimePlanValidationManager
from omnilocal_runtime.knowledge.manager import RuntimeKnowledgeManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.authorization.models import (
    RuntimeExecutionAuthorization,
    RuntimeAuthorizationCondition
)
from omnilocal_runtime.authorization.evaluator import RuntimeAuthorizationEvaluator


class RuntimeAuthorizationManager:
    """
    Gestor de la Capa de Autorización de Ejecución (Runtime Block 13).
    Determina si un plan validado puede avanzar hacia una futura ejecución.
    
    Reglas de la capa:
    - Evalúa validaciones existentes y métricas de contexto.
    - Aplica políticas de autorización y verifica restricciones.
    - Genera una autorización o rechazo con su debido razonamiento.
    - Registra la decisión de autorización y sus condiciones en SQLite.
    
    Invariantes estrictos:
    - NO ejecuta acciones reales.
    - NO modifica planes originales.
    - NO cambia decisiones ni validaciones anteriores.
    - NO altera datos históricos.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        validation_manager: Optional[RuntimePlanValidationManager] = None,
        knowledge_manager: Optional[RuntimeKnowledgeManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.validation_manager = validation_manager or RuntimePlanValidationManager(db_manager=self.db_manager)
        self.knowledge_manager = knowledge_manager or RuntimeKnowledgeManager(db_manager=self.db_manager)
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)

    def authorize_plan(
        self,
        plan_id: Optional[int] = None,
        validation_id: Optional[int] = None,
        extra_checks: Optional[List[Dict[str, Any]]] = None
    ) -> RuntimeExecutionAuthorization:
        """
        Evalúa y autoriza (o rechaza) la ejecución de un plan basándose en su reporte de validación.
        """
        # 1. Obtener o generar la validación del plan
        val_report_dict = None
        target_plan_id = plan_id or 0
        target_val_id = validation_id or 0

        if validation_id:
            all_vals = self.db_manager.get_plan_validations()
            val_report_dict = next((v for v in all_vals if v.get("id") == validation_id), None)

        if not val_report_dict and plan_id:
            val_report_obj = self.validation_manager.validate(plan_id=plan_id)
            val_report_dict = val_report_obj.to_dict()
            target_val_id = val_report_dict.get("id", 0)

        if not val_report_dict:
            # Generar una validación completa por defecto si no existía plan_id previo
            val_report_obj = self.validation_manager.validate(plan_id=plan_id)
            val_report_dict = val_report_obj.to_dict()
            target_plan_id = val_report_dict.get("plan_id", 0)
            target_val_id = val_report_dict.get("id", 0)

        if not target_plan_id:
            target_plan_id = val_report_dict.get("plan_id", 0)

        # 2. Evaluar mediante Evaluator / Policy
        confidence = 0.85
        auth_obj = RuntimeAuthorizationEvaluator.evaluate_authorization(
            validation_report=val_report_dict,
            plan_id=target_plan_id,
            validation_id=target_val_id,
            confidence_score=confidence,
            extra_checks=extra_checks
        )

        # 3. Persistir en SQLite
        app_conds_json = json.dumps(auth_obj.approved_conditions)
        rej_conds_json = json.dumps(auth_obj.rejected_conditions)

        inserted_auth_id = self.db_manager.insert_execution_authorization(
            plan_id=auth_obj.plan_id,
            validation_id=auth_obj.validation_id,
            authorization_status=auth_obj.authorization_status,
            authorization_level=auth_obj.authorization_level,
            approved_conditions=app_conds_json,
            rejected_conditions=rej_conds_json,
            reasoning=auth_obj.reasoning
        )
        auth_obj.id = inserted_auth_id

        # 4. Persistir cada condición evaluada
        for cond in auth_obj.conditions:
            cond_id = self.db_manager.insert_authorization_condition(
                authorization_id=inserted_auth_id,
                condition_name=cond.condition_name,
                condition_status=cond.condition_status,
                description=cond.description,
                severity=cond.severity
            )
            cond.id = cond_id
            cond.authorization_id = inserted_auth_id

        return auth_obj

    def get_authorization(self, authorization_id: int) -> Optional[RuntimeExecutionAuthorization]:
        """
        Recupera un registro de autorización con sus condiciones desde la base de datos.
        """
        auth_dict = self.db_manager.get_execution_authorization(authorization_id)
        if not auth_dict:
            return None

        conds_dicts = self.db_manager.get_authorization_conditions(authorization_id)
        auth_dict["conditions"] = conds_dicts
        return RuntimeExecutionAuthorization.from_dict(auth_dict)

    def get_authorizations(self) -> List[RuntimeExecutionAuthorization]:
        """
        Recupera todas las autorizaciones registradas en el sistema.
        """
        rows = self.db_manager.get_execution_authorizations()
        result = []
        for r in rows:
            c_rows = self.db_manager.get_authorization_conditions(r["id"])
            r["conditions"] = c_rows
            result.append(RuntimeExecutionAuthorization.from_dict(r))
        return result
