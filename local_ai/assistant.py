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
Bloque 5 (Semantic Retrieval Integration, ver retrieval/hybrid.py): el
contexto final que recibe el modelo, cuando hace falta llamarlo, se
enriquece con búsqueda semántica combinada con la léxica -- nunca antes
de descartar coincidencia directa o detección de hechos.

Bloque 6 (Adaptive Memory Consolidation, ver local_ai/memory_consolidation.py):
los hechos detectados por reglas ya no se insertan a ciegas -- nombre y
ocupación se actualizan en el lugar (con historial de qué decían antes);
proyecto, preferencia y otros se deduplican pero nunca se sobreescriben
entre sí. Además se registra, de forma aproximada, qué memorias fueron
relevantes para cada turno de conversación (conversation_memory_usage).
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.engine import OmniLocalEngine
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError
from local_ai.memory_detector import detect_by_rules, looks_like_question
from local_ai.memory_consolidation import consolidate_fact, extract_category
from local_ai.feedback_learning import apply_feedback_to_memories
from local_ai.context_builder import build_context
from local_ai.embeddings import generate_and_store_embedding_async
from local_ai.goal_detector import detect_goal_creation, detect_goal_update, find_matching_pending_goal
from local_ai.global_context_detector import detect_global_context_query, format_section_answer
from local_ai.synthesis_detector import detect_synthesis_query
from local_ai.code_explainer import (
    detect_explain_request, find_matching_project_file, read_file_content,
    build_explanation_context, FileReadResult,
)
from local_ai.code_reviewer import detect_review_request, _REVIEW_SYSTEM_PROMPT
from local_ai.project_search import (
    search_project_content, find_files_importing, get_file_imports,
    detect_search_request, detect_import_relation_request,
)
from local_ai.code_comparator import detect_compare_request, _COMPARE_SYSTEM_PROMPT
from local_ai.change_proposer import detect_change_proposal_request, build_project_overview, _PROPOSAL_SYSTEM_PROMPT
from local_ai.profile_digest import build_profile_digest, format_profile_digest_as_text, DEFAULT_MAX_DIGEST_CHARS
from retrieval.hybrid import hybrid_context
from goals.manager import GoalManager
from project.manager import ProjectManager
from local_ai.project_context_detector import detect_project_switch, find_matching_project
from app.logger import get_logger

logger = get_logger(__name__)

# Bloque 11C: instrucción estricta para pedidos de síntesis -- traduce la
# restricción de producto "sin prioridades automáticas, sin
# recomendaciones no solicitadas" en algo que el modelo puede seguir.
_SYNTHESIS_SYSTEM_PROMPT = (
    "Tenés información guardada sobre el usuario. Resumila de forma clara "
    "y organizada, respondiendo específicamente lo que se te preguntó. "
    "NO sugieras acciones, NO priorices qué debería hacer primero, NO "
    "agregues recomendaciones que no se pidieron explícitamente -- solo "
    "describí lo que ya se sabe."
)

# Bloque 17: mismo criterio -- traduce "solo explicar, no opinar" en una
# instrucción concreta para el modelo, no solo una intención de diseño.
_EXPLAIN_SYSTEM_PROMPT = (
    "Tenés el contenido de un archivo de código y su estructura (clases, "
    "funciones, imports). Explicá qué hace: qué contiene, para qué sirve, "
    "cómo se relaciona con lo que importa. NO opines si está bien o mal "
    "diseñado, NO sugieras cambios ni mejoras -- eso es una etapa aparte. "
    "Solo explicá qué hace, de forma clara."
)


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
        self.goal_manager = GoalManager(db_manager=self.engine.db_manager)
        self.project_manager = ProjectManager(db_manager=self.engine.db_manager)

    # ------------------------------------------------------------------
    # Enseñanza explícita ("recordá que...")
    # ------------------------------------------------------------------
    def remember(self, content: str, memory_type: str = "hecho", importance: float = 0.7) -> int:
        """Guarda algo explícitamente en la memoria local, a pedido del usuario."""
        mem_id = self.engine.save_memory(content=content, memory_type=memory_type, importance=importance)
        self._embed_async(mem_id, content)
        return mem_id

    def feedback(self, conversation_id: int, useful: bool) -> None:
        """
        Registra si una respuesta fue útil o no. Insumo para mejorar el
        sistema a futuro. Bloque 7 (Feedback Confidence Learning): además
        ajusta la confianza de las memorias que participaron en esa
        respuesta (ver local_ai/feedback_learning.py) -- no toca la
        importancia (Bloque 3), son conceptos distintos a propósito.
        """
        self.engine.db_manager.insert_chat_feedback(conversation_id=conversation_id, useful=useful)
        try:
            apply_feedback_to_memories(self.engine, conversation_id, useful)
        except Exception as exc:  # el registro del feedback no debe romperse por esto
            logger.warning(f"No se pudo ajustar la confianza de memoria tras el feedback: {exc}")

    # ------------------------------------------------------------------
    # Pregunta principal
    # ------------------------------------------------------------------
    def ask(self, query: str, save: bool = True, session_id: Optional[int] = None) -> AssistantAnswer:
        query = (query or "").strip()
        if not query:
            return AssistantAnswer(answer="No recibí ninguna pregunta.", source="vacio")

        results = self.engine.search(query)
        context_chunks = build_context(self.engine, query, session_id=session_id)

        # Bloque 16 (Project Context Binding): activación explícita de
        # proyecto ("trabajemos en X") -- se revisa primero, antes que
        # todo lo demás, mismo criterio de siempre: una intención de
        # cambiar de contexto no debe poder quedar tapada. Solo reglas,
        # cero modelo. Requiere session_id para persistir el vínculo --
        # sin sesión, no hay dónde guardarlo.
        project_switch_text = detect_project_switch(query)
        if project_switch_text is not None:
            if session_id is None:
                answer = "No puedo activar un proyecto sin una sesión de charla activa."
            else:
                projects = self.project_manager.list_projects()
                matched_project = find_matching_project(projects, project_switch_text)
                if matched_project is None:
                    answer = "No estoy seguro a qué proyecto te referís."
                else:
                    self.engine.db_manager.set_session_project(session_id, matched_project.id)
                    answer = f"Listo, activé el proyecto '{matched_project.name}'."
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Bloque 9/10 (Goal & Reminder): "recordame que..." / "cambiar X
        # para Y" son intenciones distintas de un hecho sobre el usuario
        # (Bloque 1) -- se revisan primero, también solo con reglas, sin
        # modelo. Igual criterio que el Bloque 1: una intención nueva no
        # debe poder quedar tapada por nada de lo que venga después.
        #
        # Se chequea primero ACTUALIZACIÓN, después CREACIÓN: son sets de
        # patrones separados que no deberían solaparse en la práctica
        # ("cambiar X para Y" vs. "recordame que X"), pero el orden importa
        # si alguna vez llegaran a coincidir.
        update_candidate = detect_goal_update(query)
        if update_candidate is not None:
            pending = self.goal_manager.list_pending()
            matched_goal = find_matching_pending_goal(pending, update_candidate.reference_text)
            if matched_goal is None:
                answer = "No estoy seguro de cuál objetivo querés modificar."
            else:
                new_due_at = update_candidate.new_due_at.isoformat() if update_candidate.new_due_at else None
                self.goal_manager.update_goal(matched_goal.id, due_at=new_due_at)
                answer = f"Listo, actualicé '{matched_goal.content}'."
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

        goal_candidate = detect_goal_creation(query)
        if goal_candidate is not None:
            due_at_str = goal_candidate.due_at.isoformat() if goal_candidate.due_at else None
            self.goal_manager.create_goal(
                goal_candidate.title, due_at=due_at_str,
                goal_type=goal_candidate.goal_type, category=goal_candidate.category,
            )
            answer = f"Listo, lo anoté como pendiente: {goal_candidate.title}"
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

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
            mem_id = consolidate_fact(self.engine, rule_candidate, ollama=self.ollama)
            self._embed_async(mem_id, rule_candidate.content)
            answer = self._generate_with_model(query, context_chunks) if self.ollama.ensure_running() else None
            if answer is None:
                answer = f"Listo, lo guardé: {rule_candidate.content}"
                source, used_model = "memoria_local", False
            else:
                source, used_model = "modelo_ia", True
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            self._log_memory_usage(conv_id, results)
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, context_used=context_chunks, conversation_id=conv_id)

        # Bloque 11B (Personal Context Awareness): preguntas de "vista
        # global" ("¿qué proyectos tengo?") deben responderse con TODAS
        # las memorias de esa categoría, no con la que hubiera encontrado
        # una coincidencia léxica puntual (Paso 1, abajo) -- por eso esto
        # corre ANTES. Si no se detecta acá, el orden importa: correrlo
        # después dejaría pasar el mismo tipo de error que ya arreglamos
        # en los Bloques 1 y 8 (una intención especial tapada por un
        # match genérico). Solo reglas conocidas -- nunca adivina
        # (ver global_context_detector.py, regla de ambigüedad).
        global_query = detect_global_context_query(query)
        if global_query is not None:
            digest = build_profile_digest(self.engine, self.goal_manager)
            answer = format_section_answer(digest, global_query)
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Paso 1: ¿hay una coincidencia directa ya guardada? No se usa el modelo.
        direct = self._find_direct_match(query, results)
        if direct is not None:
            conv_id = self._log_conversation(query, direct, session_id) if save else None
            self._log_memory_usage(conv_id, results)
            return AssistantAnswer(answer=direct, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Bloque 8 (Semantic Direct Memory Response Layer): solo se intenta
        # si el léxico no encontró nada. Salvaguardas fuertes adentro del
        # método (solo preguntas, solo nombre/ocupacion, confidence alta,
        # umbral de similitud alto) -- ver docstring de
        # _find_semantic_direct_match. _find_direct_match no se tocó.
        semantic_direct = self._find_semantic_direct_match(self.engine, query, self.ollama)
        if semantic_direct is not None:
            conv_id = self._log_conversation(query, semantic_direct, session_id) if save else None
            self._log_memory_usage(conv_id, results)
            return AssistantAnswer(answer=semantic_direct, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Bloque 11C (Personal Context Synthesis): pedidos explícitos de
        # resumen ("dame un resumen", "qué sabés de mí") usan el digest
        # COMPLETO (Bloque 11A), no el top-N por relevancia de
        # hybrid_context -- por eso es una rama separada, no una variante
        # del camino general de abajo. Corre después de las coincidencias
        # directas (no compite con ellas: nada de lo que matchea acá se
        # parece a un hecho puntual). Sin Ollama, degrada al listado plano
        # del digest en vez de un error -- sigue siendo información real y
        # útil, mismo criterio que el resto del proyecto.
        if detect_synthesis_query(query):
            digest = build_profile_digest(self.engine, self.goal_manager)
            digest_text = format_profile_digest_as_text(digest, max_chars=DEFAULT_MAX_DIGEST_CHARS)
            answer = None
            if self.ollama.ensure_running():
                answer = self._generate_with_model(query, [digest_text], system=_SYNTHESIS_SYSTEM_PROMPT)
            if answer is None:
                answer = digest_text
                source, used_model = "memoria_local", False
            else:
                source, used_model = "modelo_ia", True
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, conversation_id=conv_id)

        # Bloque 17 (Code Explanation): "explicame X.py" -- usa el proyecto
        # activo de la sesión (Bloque 16) y la estructura ya extraída
        # (Bloque 15). Solo lectura: no edita ni ejecuta nada, no opina
        # sobre calidad (eso es una etapa aparte). No compite con las
        # coincidencias directas de arriba, mismo motivo que el Bloque 11C.
        # Bloque 18 (Code Review asistido): "revisá X.py" / "analizame X.py"
        # -- se chequea ANTES que el Bloque 17 porque "analizá" se movió
        # acá (encaja mejor semánticamente con opinar que con explicar).
        # Mismo mecanismo que el 17 (proyecto activo, buscar archivo, leer
        # contenido), pero acá el prompt SÍ le pide al modelo que opine --
        # nunca modifica nada, solo lectura, igual que el 17.
        # Bloque 19 (Exploración segura): búsqueda de contenido y
        # relaciones por imports son DETERMINÍSTICAS -- cero modelo, se
        # revisan antes que todo lo que sí lo necesita. Requieren proyecto
        # activo (Bloque 16), igual que 17/18.
        search_term = detect_search_request(query)
        if search_term is not None:
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None
            if not active_project_id:
                answer = "Primero activá un proyecto (\"trabajemos en X\" o /proyecto usar <id>)."
            else:
                project = self.project_manager.get_project(active_project_id)
                matches = search_project_content(project.path, search_term) if project else []
                if not matches:
                    answer = f"No encontré coincidencias para '{search_term}' en el proyecto."
                else:
                    listado = "\n".join(f"  {m.relative_path}:{m.line_number}: {m.snippet}" for m in matches)
                    answer = f"Encontré {len(matches)} coincidencia(s):\n{listado}"
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

        import_relation = detect_import_relation_request(query)
        if import_relation is not None:
            kind, value = import_relation
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None
            if not active_project_id:
                answer = "Primero activá un proyecto (\"trabajemos en X\" o /proyecto usar <id>)."
            else:
                project_files = self.engine.db_manager.get_project_files(active_project_id)
                if kind == "who_imports":
                    files = find_files_importing(project_files, value)
                    answer = (f"Archivos que importan '{value}': " + ", ".join(f["relative_path"] for f in files)) if files else f"Ningún archivo importa '{value}'."
                else:
                    matched_file = find_matching_project_file(project_files, value)
                    if matched_file is None:
                        answer = "No estoy seguro a qué archivo te referís."
                    else:
                        imports = get_file_imports(project_files, matched_file["relative_path"]) or []
                        answer = f"{matched_file['relative_path']} importa: " + (", ".join(imports) if imports else "nada.")
            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source="memoria_local", used_model=False, conversation_id=conv_id)

        # Comparar dos archivos SÍ necesita el modelo -- misma mecánica de siempre.
        compare_files = detect_compare_request(query)
        if compare_files is not None:
            file_a_name, file_b_name = compare_files
            source, used_model = "sin_modelo", False
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None

            if not active_project_id:
                answer = "Primero activá un proyecto (\"trabajemos en X\" o /proyecto usar <id>)."
            else:
                project_files = self.engine.db_manager.get_project_files(active_project_id)
                file_a = find_matching_project_file(project_files, file_a_name)
                file_b = find_matching_project_file(project_files, file_b_name)
                if file_a is None or file_b is None:
                    answer = "No estoy seguro a qué archivo(s) te referís."
                else:
                    project = self.project_manager.get_project(active_project_id)
                    read_a = read_file_content(os.path.join(project.path, file_a["relative_path"])) if project else FileReadResult(None, False, "Proyecto no encontrado")
                    read_b = read_file_content(os.path.join(project.path, file_b["relative_path"])) if project else FileReadResult(None, False, "Proyecto no encontrado")
                    if read_a.error or read_b.error:
                        answer = f"No pude leer alguno de los archivos: {read_a.error or read_b.error}."
                    else:
                        compare_context = [
                            f"Archivo A ({file_a['relative_path']}):\n{read_a.content}",
                            f"Archivo B ({file_b['relative_path']}):\n{read_b.content}",
                        ]
                        model_answer = self._generate_with_model(query, compare_context, system=_COMPARE_SYSTEM_PROMPT) if self.ollama.ensure_running() else None
                        if model_answer is not None:
                            answer, source, used_model = model_answer, "modelo_ia", True
                        else:
                            answer = "No pude generar la comparación (¿Ollama está corriendo?)."

            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, conversation_id=conv_id)

        review_filename = detect_review_request(query)
        if review_filename is not None:
            source, used_model = "sin_modelo", False
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None

            if not active_project_id:
                answer = "Primero activá un proyecto (\"trabajemos en X\" o /proyecto usar <id>)."
            else:
                project_files = self.engine.db_manager.get_project_files(active_project_id)
                matched_file = find_matching_project_file(project_files, review_filename)
                if matched_file is None:
                    answer = "No estoy seguro a qué archivo te referís."
                else:
                    project = self.project_manager.get_project(active_project_id)
                    full_path = os.path.join(project.path, matched_file["relative_path"]) if project else None
                    read_result = read_file_content(full_path) if full_path else FileReadResult(None, False, "Proyecto no encontrado")
                    if read_result.error or not read_result.content:
                        answer = f"No pude leer ese archivo: {read_result.error or 'contenido vacío'}."
                    else:
                        review_context = build_explanation_context(matched_file, read_result.content, read_result.truncated)
                        model_answer = self._generate_with_model(query, review_context, system=_REVIEW_SYSTEM_PROMPT) if self.ollama.ensure_running() else None
                        if model_answer is not None:
                            answer, source, used_model = model_answer, "modelo_ia", True
                        else:
                            answer = "No pude generar la revisión (¿Ollama está corriendo?)."

            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, conversation_id=conv_id)

        explain_filename = detect_explain_request(query)
        if explain_filename is not None:
            source, used_model = "sin_modelo", False
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None

            if not active_project_id:
                answer = "Primero activá un proyecto (\"trabajemos en X\" o /proyecto usar <id>)."
            else:
                project_files = self.engine.db_manager.get_project_files(active_project_id)
                matched_file = find_matching_project_file(project_files, explain_filename)
                if matched_file is None:
                    answer = "No estoy seguro a qué archivo te referís."
                else:
                    project = self.project_manager.get_project(active_project_id)
                    full_path = os.path.join(project.path, matched_file["relative_path"]) if project else None
                    read_result = read_file_content(full_path) if full_path else FileReadResult(None, False, "Proyecto no encontrado")
                    if read_result.error or not read_result.content:
                        answer = f"No pude leer ese archivo: {read_result.error or 'contenido vacío'}."
                    else:
                        explanation_context = build_explanation_context(matched_file, read_result.content, read_result.truncated)
                        model_answer = self._generate_with_model(query, explanation_context, system=_EXPLAIN_SYSTEM_PROMPT) if self.ollama.ensure_running() else None
                        if model_answer is not None:
                            answer, source, used_model = model_answer, "modelo_ia", True
                        else:
                            answer = "No pude generar la explicación (¿Ollama está corriendo?)."

            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, conversation_id=conv_id)

        # Bloque 20 (Propuestas de cambios): el más amplio de la familia
        # de detectores de proyecto -- no ancla en un archivo puntual como
        # 17/18/comparador, por eso se revisa último (si el mensaje
        # mencionaba un archivo concreto, esos ya lo habrían resuelto
        # antes). Usa la ESTRUCTURA de TODO el proyecto (Bloque 15), no
        # contenido -- no escribe ni ejecuta nada, ni siquiera un diff.
        # Ajuste de la aprobación: sin proyecto activo, corta ANTES de
        # tocar el modelo -- solo el mensaje pidiendo activar uno.
        change_description = detect_change_proposal_request(query)
        if change_description is not None:
            source, used_model = "sin_modelo", False
            session = self.engine.db_manager.get_chat_session(session_id) if session_id else None
            active_project_id = session.get("active_project_id") if session else None

            if not active_project_id:
                answer = "Necesito que actives un proyecto primero."
            else:
                project = self.project_manager.get_project(active_project_id)
                project_files = self.engine.db_manager.get_project_files(active_project_id)
                if project is None or not project_files:
                    answer = "Todavía no tengo archivos analizados de ese proyecto (¿corriste /proyecto agregar?)."
                else:
                    overview = build_project_overview(project, project_files)
                    model_answer = self._generate_with_model(query, [overview], system=_PROPOSAL_SYSTEM_PROMPT) if self.ollama.ensure_running() else None
                    if model_answer is not None:
                        answer, source, used_model = model_answer, "modelo_ia", True
                    else:
                        answer = "No pude generar la propuesta (¿Ollama está corriendo?)."

            conv_id = self._log_conversation(query, answer, session_id) if save else None
            return AssistantAnswer(answer=answer, source=source, used_model=used_model, conversation_id=conv_id)

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

        # Bloque 5 (Semantic Retrieval Integration): recién acá, con Ollama ya
        # confirmado disponible y sabiendo que sí o sí se va a llamar al
        # modelo, se enriquece el contexto con búsqueda semántica (híbrida
        # con lo léxico). Nunca antes de este punto: ni la detección de
        # hechos por reglas ni la coincidencia directa deben gastar
        # embeddings. Si no hay modelo de embeddings o algo falla,
        # hybrid_context devuelve context_chunks tal cual (mismo
        # comportamiento que antes de este bloque).
        context_chunks = hybrid_context(self.engine, query, self.ollama, context_chunks)

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
            self._log_memory_usage(conv_id, results)

        return AssistantAnswer(answer=answer, source="modelo_ia", used_model=True, context_used=context_chunks, conversation_id=conv_id)

    def _log_memory_usage(self, conv_id: Optional[int], results) -> None:
        """
        Trazabilidad aproximada (Bloque 6): registra qué memorias eran
        relevantes para la consulta de este turno. Es una aproximación (no
        necesariamente exactamente lo que terminó en el prompt final del
        modelo, que puede truncarse en build_context/hybrid_context) --
        deliberado, para no tener que tocar esos dos módulos ya estables.
        """
        if not conv_id or not results:
            return
        try:
            for r in results:
                if r.source_type == "memory" and r.id is not None:
                    self.engine.db_manager.insert_conversation_memory_usage(conv_id, r.id)
        except Exception as exc:  # nunca debe romper el flujo principal de la conversación
            logger.warning(f"No se pudo registrar la trazabilidad de memoria: {exc}")

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

    def _generate_with_model(self, query: str, context_chunks: List[str], system: Optional[str] = None) -> Optional[str]:
        """Llama al modelo local; devuelve None si no hay respuesta aprovechable (sin lanzar excepción)."""
        try:
            answer = self.ollama.generate(prompt=query, context_chunks=context_chunks, system=system)
        except OllamaUnavailableError as exc:
            logger.warning(f"Fallo al generar respuesta con el modelo local: {exc}")
            return None
        return answer.strip() if answer and answer.strip() else None

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

    # Categorías elegibles para respuesta semántica directa (Bloque 8):
    # solo "casillas de valor único" (Bloque 6) -- nunca colecciones
    # (proyecto/preferencia/otro), donde "cuál de varios" es ambiguo.
    SEMANTIC_DIRECT_MATCH_CATEGORIES = {"nombre", "ocupacion"}

    @staticmethod
    def _find_semantic_direct_match(
        engine,
        query: str,
        ollama,
        min_similarity: float = 0.85,
        min_confidence: float = 0.7,
    ) -> Optional[str]:
        """
        Bloque 8 (Semantic Direct Memory Response Layer): extiende la idea
        de "coincidencia directa" (ver _find_direct_match, que NO se toca)
        a memorias encontradas por similitud semántica, con salvaguardas
        estrictas porque acá no hay ningún modelo que revise la respuesta
        antes de mostrarla:

        1. Solo se intenta si la consulta TIENE FORMA DE PREGUNTA
           (looks_like_question). Es la protección más importante: una
           declaración nueva ("mi nombre es Marcos") nunca debe poder
           confundirse con "esto ya lo sé, respondo directo" -- eso
           reabriría el mismo tipo de bug del Bloque 1, pero para el caso
           semántico. Las declaraciones se resuelven en rule_candidate,
           antes de llegar acá.
        2. Solo memorias tipo "hecho" de categoría nombre/ocupacion (nunca
           colecciones: proyecto/preferencia/otro son ambiguas -- "cuál de
           varios" no se puede responder sin que el modelo elija).
        3. Solo si `confidence` (Bloque 7) de esa memoria es alta -- una
           memoria con feedback negativo no responde sola, sin revisión.
        4. Umbral de similitud alto (0.85 por defecto) -- mucho más
           estricto que el 0.5 que usa hybrid_context() para armar
           contexto (ahí un falso positivo es barato; acá no hay ningún
           chequeo posterior).
        5. Si no hay modelo de embeddings, ni se intenta -- cero llamadas
           de red de más.
        """
        if not looks_like_question(query):
            return None
        if not ollama.has_embedding_model():
            return None

        try:
            semantic_results = engine.retrieval_engine.search_semantic(query, ollama, min_similarity=min_similarity)
        except OllamaUnavailableError:
            return None
        except Exception:
            return None

        for r in semantic_results:
            memory = engine.memory_manager.get_memory(r.id)
            if memory is None or memory.memory_type != "hecho":
                continue
            category = extract_category(memory.content)
            if category not in LocalAssistant.SEMANTIC_DIRECT_MATCH_CATEGORIES:
                continue
            if memory.confidence < min_confidence:
                continue
            return memory.content

        return None

    def _log_conversation(self, query: str, answer: str, session_id: Optional[int] = None) -> Optional[int]:
        try:
            return self.engine.db_manager.insert_conversation(
                user_input=query, assistant_response=answer, session_id=session_id
            )
        except Exception as exc:  # el historial de conversación no debe romper la respuesta
            logger.warning(f"No se pudo registrar la conversación: {exc}")
            return None
