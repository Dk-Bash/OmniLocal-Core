from typing import List, Optional
from retrieval.engine import RetrievalEngine
from user.manager import UserManager
from context.manager import ContextManager
from personalization.models import PersonalizedResult
from app.logger import get_logger

logger = get_logger("personalization.engine")


class PersonalizedRetrievalEngine:
    """
    Motor de recuperación personalizada para OmniLocal-Core.
    Integra el motor de búsqueda base (RetrievalEngine) con información del usuario
    (UserManager) y el contexto de la conversación activa (ContextManager) para
    ajustar los puntajes de relevancia y justificar las coincidencias.

    Cumple con la regla arquitectónica de NO escribir SQL directo.
    """

    def __init__(
        self,
        retrieval_engine: Optional[RetrievalEngine] = None,
        user_manager: Optional[UserManager] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.retrieval_engine = retrieval_engine or RetrievalEngine()
        self.user_manager = user_manager or UserManager(db_manager=self.retrieval_engine.memory_manager.db_manager)
        self.context_manager = context_manager or ContextManager(db_manager=self.retrieval_engine.memory_manager.db_manager)
        logger.info("PersonalizedRetrievalEngine inicializado correctamente.")

    def search(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> List[PersonalizedResult]:
        """
        Realiza una búsqueda personalizada combinando resultados de recuperación básica
        con preferencias del usuario e historial de la sesión de contexto activa.
        """
        # 1. Obtener resultados base desde RetrievalEngine
        base_results = self.retrieval_engine.search(query)

        # 2. Obtener datos del usuario si se especifica user_id
        user_profile = None
        user_preferences = []
        if user_id is not None:
            user_profile = self.user_manager.get_profile(user_id)
            user_preferences = self.user_manager.get_preferences(user_id)

        # 3. Obtener contexto activo si se especifica session_id
        recent_messages = []
        if session_id is not None:
            recent_messages = self.context_manager.get_recent_messages(session_id)

        personalized_results = []

        for base_res in base_results:
            base_score = base_res.score if base_res.score is not None else 0.8
            score = base_score
            reasons = []

            # Evaluación de contexto
            if recent_messages:
                context_text = " ".join([m.content.lower() for m in recent_messages])
                if query.lower() in context_text or any(word.lower() in context_text for word in query.split()):
                    score += 0.15
                    reasons.append("Relacionado con contexto actual")

            # Evaluación de usuario y preferencias
            if user_preferences or user_profile:
                pref_text = " ".join([p.value.lower() for p in user_preferences] + ([user_profile.language.lower()] if user_profile else []))
                if query.lower() in pref_text or any(word.lower() in pref_text for word in query.split()):
                    score += 0.1
                    reasons.append("Coincide con preferencias del usuario")
                else:
                    reasons.append("Relacionado con preferencias del usuario")

            if not reasons:
                reasons.append("Coincidencia de búsqueda estándar")

            final_score = min(1.0, round(score, 2))
            reason_str = " | ".join(reasons)

            personalized_results.append(
                PersonalizedResult(
                    id=base_res.id,
                    source_type=base_res.source_type,
                    content=base_res.content,
                    relevance_score=final_score,
                    reason=reason_str
                )
            )

        # Ordenar por puntaje de relevancia descendente
        personalized_results.sort(key=lambda r: r.relevance_score, reverse=True)
        logger.info(f"Búsqueda personalizada completada para '{query}' ({len(personalized_results)} resultados).")
        return personalized_results
