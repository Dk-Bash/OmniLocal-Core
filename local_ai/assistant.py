"""
Asistente local de OmniLocal-Core.

Combina lo que el sistema ya tiene (memorias y nodos de conocimiento,
recuperados por RetrievalEngine) con un modelo de lenguaje que corre
100% en la máquina del usuario (vía Ollama). No hay llamadas a APIs
externas ni a ninguna IA en la nube en ningún punto de este módulo.

Estrategia para no depender del modelo salvo que haga falta:
1. Si la pregunta ya tiene una respuesta guardada (memoria o conocimiento
   que contiene literalmente lo preguntado), se devuelve directo. Cero uso
   del modelo de IA.
2. Si no hay una coincidencia directa, se arma un prompt con el contexto
   recuperado (RAG) y recién ahí se invoca al modelo local.
3. Toda respuesta generada por el modelo se guarda como memoria nueva, así
   la próxima vez que se pregunte algo parecido, el paso 1 alcanza y no
   hace falta volver a invocar al modelo. Así es como el sistema "aprende"
   con el uso, sin ningún componente externo.

Bloque 1 (memoria automática, ver local_ai/memory_detector.py): antes de
guardar la respuesta como charla genérica, se revisa (con reglas, sin
gastar el modelo) si lo que escribió el usuario contiene un dato
reutilizable (nombre, ocupación, proyecto, preferencia). Si lo encuentra,
se guarda como "hecho" con más peso; si no, se conserva el comportamiento
anterior. `detect_by_model` (clasificación vía IA) existe y está probado en
local_ai/memory_detector.py, pero no se invoca desde este flujo en vivo: se
gastaba una llamada al modelo para clasificar aunque la respuesta ya
existiera guardada, rompiendo la prioridad "si hay memoria directa, nunca
se usa el modelo".

Bloque 2 (contexto conversacional, ver local_ai/context_builder.py): el
contexto que se le pasa al modelo ya no es solo memoria/conocimiento
(RAG) -- también incluye los últimos turnos de la sesión activa, para que
el modelo pueda resolver referencias como "agregale memoria a ESO" cuando
"eso" se mencionó en el mensaje anterior de la misma charla. Sesiones
distintas nunca se mezclan entre sí.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.engine import OmniLocalEngine
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from local_ai.memory_detector import detect_by_rules
from local_ai.context_builder import build_context
from local_ai.embeddings import generate_and_store_embedding_async
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AssistantAnswer:
    answer: str
    source: str  # "memoria_local" | "modelo_ia" | "sin_modelo" | "vacio"
    used_model: bool = False
    context_used: List[str] = field(default_factory=list)
    conversation_id: Optional[int] = None


class LocalAssistant:
    """
    Punto de entrada único para "hacerle una pregunta" a OmniLocal-Core.
    """

    def __init__(
        self,
        engine: Optional[OmniLocalEngine] = None,
        ollama_client: Optional[OllamaClient] = None,
        max_context_results: int = 5,
    ):
        self.engine = engine or OmniLocalEngine()
        self.ollama = ollama_client or OllamaClient()
        self.max_context_results = max_context_results

    # ------------------------------------------------------------------
    # Enseñanza explícita ("recordá que...")
    # ------------------------------------------------------------------
    def remember(self, content: str, memory_type: str = "hecho", importance: float = 0.7) -> int:
        """Guarda algo explícitamente en la memoria local, a pedido del usuario."""
        mem_id = self.engine.save_memory(content=content, memory_type=memory_type, importance=importance)
        self._embed_async(mem_id, content)
        return mem_id

    def feedback(self, conversation_id: int, useful: bool) -> None:
        """Registra si una respuesta fue útil o no. Insumo para mejorar el sistema a futuro."""
        self.engine.db_manager.insert_chat_feedback(conversation_id=conversation_id, useful=useful)

    # ------------------------------------------------------------------
    # Pregunta principal
    # ------------------------------------------------------------------
    def ask(self, query: str, save: bool = True, session_id: Optional[int] = None) -> AssistantAnswer:
        query = (query or "").strip()
        if not query:
            return AssistantAnswer(answer="No recibí ninguna pregunta.", source="vacio")

        results = self.engine.search(query)
        context_chunks = build_context(self.engine, query, session_id=session_id)

        # Bloque 1: si el mensaje declara un dato nuevo (no es una pregunta),
        # se guarda siempre -- con o sin modelo disponible -- ANTES de mirar
        # si hay una memoria vieja parecida. Si esto se hiciera después del
        # paso de "coincidencia directa", un mensaje como "Mi nombre es
        # Marcelo y trabajo en ICQA" podía terminar devolviendo una charla
        # vieja no relacionada (por compartir la palabra "nombre") y el dato
        # nuevo ("trabajo en ICQA") se perdía sin guardarse nunca.
        #
        # Se usa acá SOLO el camino de reglas (detect_by_rules), no
        # detect_memory_candidate completo: ese último intenta primero
        # clasificar con el modelo, lo que rompía la prioridad "si ya hay
        # memoria directa, nunca se usa el modelo" -- el detector gastaba
        # una llamada a Ollama para clasificar aunque la respuesta ya
        # existiera guardada. Las reglas son instantáneas y sin red, así
        # que no tienen ese costo.
        rule_candidate = detect_by_rules(query)
        if rule_candidate is not None:
            mem_id = self.engine.save_memory(
                content=rule_candidate.content, memory_type=rule_candidate.memory_type, importance=rule_candidate.importance
            )
            self._embed_async(mem_id, rule_candidate.content)
            answer = self._generate_with_model(query, context_chunks) if self.ollama.ensure_running() else None
            if answer is None:
                answer = f"Listo, lo guardé: {rule_candidate.content}"
                source, used_model = "memoria_local", False
            else:
                source, used_model = "modelo_ia", True
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, context_used=context_chunks, conversation_id=conv_id)

        # Paso 1: ¿hay una coincidencia directa ya guardada? No se usa el modelo.
        direct = self._find_direct_match(query, results)
        if direct is not None:
            conv_id = self._log_conversation(query, direct, session_id) if save else None
            return AssistantAnswer(answer=direct, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Paso 2: no hay coincidencia directa -> usar el contexto ya armado para RAG.
        if not self.ollama.ensure_running():
            fallback = (
                "No tengo esa información guardada todavía. Traté de iniciar el "
                "modelo de IA local (Ollama) automáticamente pero no está "
                "disponible: instalalo desde https://ollama.com o revisá que "
                "el modelo esté descargado. Mientras tanto, podés enseñarme la "
                "respuesta con '/recordar <texto>'."
            )
            return AssistantAnswer(answer=fallback, source="sin_modelo", context_used=context_chunks)

        answer = self._generate_with_model(query, context_chunks)
        if answer is None:
            fallback = (
                "Tuve un problema para consultar al modelo de IA local. "
                "Verificá que Ollama esté corriendo (`ollama serve`) y que el "
                "modelo esté descargado (`ollama pull <modelo>`)."
            )
            return AssistantAnswer(answer=fallback, source="sin_modelo", context_used=context_chunks)

        # Paso 3: aprendizaje continuo -> lo generado queda guardado como memoria
        # genérica de conversación (acá no hubo un dato puntual detectado).
        conv_id = None
        if save:
            generic_content = f"P: {query}\nR: {answer}"
            mem_id = self.engine.save_memory(content=generic_content, memory_type="conversacion", importance=0.4)
            self._embed_async(mem_id, generic_content)
            conv_id = self._log_conversation(query, answer, session_id)

        return AssistantAnswer(answer=answer, source="modelo_ia", used_model=True, context_used=context_chunks, conversation_id=conv_id)

    def _embed_async(self, memory_id: int, content: str) -> None:
        """
        Dispara la generación del embedding de una memoria en segundo plano
        (Bloque 4A). No bloquea la respuesta al usuario: si Ollama no tiene
        el modelo de embeddings, o falla, la memoria queda igual guardada
        (solo que sin vector todavía). Ver local_ai/embeddings.py.
        """
        try:
            generate_and_store_embedding_async(self.engine, memory_id, content, self.ollama)
        except Exception as exc:  # nunca debe romper el flujo principal de la conversación
            logger.warning(f"No se pudo iniciar la generación de embedding en segundo plano: {exc}")

    def _generate_with_model(self, query: str, context_chunks: List[str]) -> Optional[str]:
        """Llama al modelo local; devuelve None si no hay respuesta aprovechable (sin lanzar excepción)."""
        try:
            answer = self.ollama.generate(prompt=query, context_chunks=context_chunks)
        except OllamaUnavailableError as exc:
            logger.warning(f"Fallo al generar respuesta con el modelo local: {exc}")
            return None
        return answer.strip() if answer and answer.strip() else None

        return AssistantAnswer(answer=answer, source="modelo_ia", used_model=True, context_used=context_chunks, conversation_id=conv_id)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    @staticmethod
    def _find_direct_match(query: str, results, min_score: float = 0.6) -> Optional[str]:
        """
        Un resultado se considera 'coincidencia directa' si cubre la mayoría
        de las palabras clave de la consulta (score >= min_score, ver
        RetrievalEngine). En ese caso no hace falta invocar al modelo de IA:
        la respuesta ya se sabe. Los resultados llegan ordenados por score
        descendente, así que alcanza con mirar el primero.
        """
        if not results:
            return None
        best = results[0]
        if best.score >= min_score and best.content:
            return best.content
        return None

    def _log_conversation(self, query: str, answer: str, session_id: Optional[int] = None) -> Optional[int]:
        try:
            return self.engine.db_manager.insert_conversation(
                user_input=query, assistant_response=answer, session_id=session_id
            )
        except Exception as exc:  # el historial de conversación no debe romper la respuesta
            logger.warning(f"No se pudo registrar la conversación: {exc}")
            return None
