from datetime import datetime
from typing import List, Optional
from personalization.engine import PersonalizedRetrievalEngine
from context.manager import ContextManager
from memory.manager import MemoryManager
from orchestration.models import InteractionResult
from app.logger import get_logger

logger = get_logger("orchestration.engine")


class OrchestratorEngine:
    """
    Capa central de orquestación (OmniLocal Orchestration Layer).
    Coordina el flujo completo de interacción entre la sesión de contexto actual,
    el motor de recuperación personalizada y el registro de memoria episódica.

    Respeta las reglas arquitectónicas: Cero consultas SQL directas.
    """

    def __init__(
        self,
        personalized_engine: Optional[PersonalizedRetrievalEngine] = None,
        context_manager: Optional[ContextManager] = None,
        memory_manager: Optional[MemoryManager] = None
    ):
        self.personalized_engine = personalized_engine or PersonalizedRetrievalEngine()
        self.context_manager = context_manager or self.personalized_engine.context_manager
        self.memory_manager = memory_manager or self.personalized_engine.retrieval_engine.memory_manager
        logger.info("OrchestratorEngine inicializado correctamente.")

    def process_interaction(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> InteractionResult:
        """
        Procesa una interacción completa del usuario:
        1. Registra el mensaje en ContextManager si existe una sesión activa.
        2. Ejecuta la búsqueda personalizada con PersonalizedRetrievalEngine.
        3. Registra el resultado de la interacción como una memoria episódica en MemoryManager.
        4. Devuelve un InteractionResult con los detalles consolidados.
        """
        logger.info(f"Procesando interacción para consulta '{query}' (User ID: {user_id}, Session ID: {session_id}).")

        # Paso 1: Registrar mensaje del usuario en el contexto conversacional activo
        if session_id is not None:
            self.context_manager.add_message(session_id, "user", query)

        # Paso 2: Ejecutar recuperación personalizada
        retrieval_results = self.personalized_engine.search(query, user_id=user_id, session_id=session_id)

        # Extraer fuentes únicas encontradas
        sources = list(set([r.source_type for r in retrieval_results]))

        # Paso 3: Guardar resultado de interacción como memoria episódica
        memory_content = f"Interacción de usuario con consulta '{query}'. {len(retrieval_results)} resultados encontrados."
        mem_id = self.memory_manager.save_memory(
            content=memory_content,
            memory_type="episodic",
            importance=0.5
        )

        # Paso 4: Construir y devolver InteractionResult
        result = InteractionResult(
            id=mem_id,
            query=query,
            results_count=len(retrieval_results),
            sources=sources,
            created_at=datetime.now()
        )

        logger.info(f"Interacción completada exitosamente. ID Memoria: {mem_id}, Resultados: {len(retrieval_results)}.")
        return result
