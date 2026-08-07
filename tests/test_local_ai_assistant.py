import os
import tempfile
from unittest.mock import patch

import pytest

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient, OllamaUnavailableError


@pytest.fixture
def engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    eng = OmniLocalEngine(db_manager=db_manager)
    eng.start()
    yield eng
    db_manager.close()
    os.remove(path)


def test_direct_memory_match_never_calls_model(engine):
    assistant = LocalAssistant(engine=engine)
    assistant.remember("El wifi de casa es RedCasa123")

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("RedCasa123")
        mock_generate.assert_not_called()

    assert result.source == "memoria_local"
    assert result.used_model is False
    assert "RedCasa123" in result.answer


def test_no_model_available_degrades_gracefully(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=False):
        result = assistant.ask("algo que no está guardado en ningún lado")

    assert result.source == "sin_modelo"
    assert "Ollama" in result.answer


def test_model_path_saves_new_memory_for_next_time(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="La respuesta generada por el modelo."):
        result = assistant.ask("una pregunta nueva")

    assert result.source == "modelo_ia"
    assert result.used_model is True

    memories = engine.get_all_memories()
    assert any("La respuesta generada por el modelo." in m.content for m in memories)

    conversations = engine.db_manager.get_conversations()
    assert len(conversations) == 1
    assert conversations[0]["assistant_response"] == "La respuesta generada por el modelo."


def test_ask_saves_detected_fact_as_hecho_instead_of_generic_conversation(engine):
    """Bloque 1: si el usuario dice un dato reutilizable, se guarda como
    'hecho' con más peso, no como charla genérica."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="¡Encantado, Marcelo!"):
        result = assistant.ask("Mi nombre es Marcelo")

    assert result.source == "modelo_ia"

    memories = engine.get_all_memories()
    hechos = [m for m in memories if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "Marcelo" in hechos[0].content
    assert hechos[0].importance == 0.75
    # No debe haber quedado también guardado como charla genérica duplicada.
    assert not any(m.memory_type == "conversacion" for m in memories)


def test_new_declaration_is_not_masked_by_unrelated_old_memory(engine):
    """Regresión: un mensaje nuevo con datos ("mi nombre es X y trabajo en
    Y") no debe devolver una charla vieja no relacionada solo porque
    comparte alguna palabra clave (ej. "nombre"), y el dato nuevo se debe
    guardar en vez de perderse."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="hola generico, contame mas"):
        assistant.ask("Bienvenido al mundo! Mi nombre es Marcelo, y el tuyo?")

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="¡Genial que trabajes en ICQA!"):
        result = assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    # No debe haber devuelto la charla vieja como si "respondiera" al mensaje nuevo.
    assert "Bienvenido al mundo" not in result.answer

    hechos = [m for m in engine.get_all_memories() if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "ICQA" in hechos[0].content


def test_direct_match_never_calls_generate_even_with_ollama_really_available(engine):
    """Regresión: si Ollama está realmente disponible (is_available=True),
    el detector no debe gastar una llamada a generate() para clasificar
    cuando la respuesta ya existe en memoria directa. Antes de este fix,
    detect_memory_candidate probaba el camino con modelo primero, y con
    Ollama de verdad corriendo eso contaba como una llamada real."""
    assistant = LocalAssistant(engine=engine)
    assistant.remember("El wifi de casa es RedCasa123")

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("RedCasa123")

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"


def test_new_declaration_without_availability_never_calls_generate(engine):
    """Regresión: si is_available() dice que no hay modelo, la rama de
    declaración nueva no debe intentar generate() en absoluto (antes lo
    intentaba sin chequear disponibilidad primero, a diferencia del resto
    del flujo)."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=False), \
         patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"


def test_direct_match_never_calls_embeddings_or_semantic_search(engine):
    """Bloque 5, Caso 4: si hay coincidencia directa, no debe llamarse ni
    embed() ni search_semantic() -- ni siquiera con el modelo de embeddings
    genuinamente disponible (misma lección que la regresión anterior con
    generate())."""
    assistant = LocalAssistant(engine=engine)
    assistant.remember("El wifi de casa es RedCasa123")

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "has_embedding_model", return_value=True), \
         patch.object(OllamaClient, "embed") as mock_embed, \
         patch("local_ai.assistant.hybrid_context") as mock_hybrid:
        result = assistant.ask("RedCasa123")

    mock_embed.assert_not_called()
    mock_hybrid.assert_not_called()
    assert result.source == "memoria_local"


def test_new_declaration_never_calls_embeddings_for_the_answer(engine):
    """Bloque 5, Caso 4 (extendido): la rama de declaración nueva tampoco
    debe pasar por la capa híbrida -- guarda y responde sin buscar
    semánticamente."""
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="dale, anotado"), \
         patch("local_ai.assistant.hybrid_context") as mock_hybrid:
        assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    mock_hybrid.assert_not_called()


def test_general_path_without_direct_match_does_use_hybrid_context(engine):
    """Contraparte del Caso 4: cuando SÍ hace falta llamar al modelo (sin
    match directo, sin dato de regla), la capa híbrida debe invocarse."""
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", return_value="respuesta generica"), \
         patch("local_ai.assistant.hybrid_context") as mock_hybrid:
        mock_hybrid.side_effect = lambda engine, query, ollama, base_context_chunks, **kw: base_context_chunks
        assistant.ask("una pregunta cualquiera sin datos personales")

    mock_hybrid.assert_called_once()


def test_new_declaration_saved_even_without_model_available(engine):
    """El dato nuevo se guarda igual aunque no haya modelo disponible."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=False):
        result = assistant.ask("Mi nombre es Marcelo y trabajo en ICQA")

    assert result.source == "memoria_local"
    hechos = [m for m in engine.get_all_memories() if m.memory_type == "hecho"]
    assert len(hechos) == 1
    assert "ICQA" in hechos[0].content


def test_model_error_returns_friendly_fallback(engine):
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=OllamaUnavailableError("boom")):
        result = assistant.ask("otra pregunta nueva")

    assert result.source == "sin_modelo"
    assert result.used_model is False


def test_empty_query_is_handled():
    assistant = LocalAssistant()
    result = assistant.ask("   ")
    assert result.source == "vacio"


def test_ensure_running_returns_true_if_already_available():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=True):
        assert client.ensure_running() is True


def test_ensure_running_returns_false_if_ollama_not_installed():
    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=False), \
         patch("local_ai.ollama_client.shutil.which", return_value=None):
        assert client.ensure_running() is False


def test_ensure_running_starts_process_when_installed_but_stopped():
    client = OllamaClient()
    availability = iter([False, False, True])
    with patch.object(OllamaClient, "is_available", side_effect=lambda: next(availability)), \
         patch("local_ai.ollama_client.shutil.which", return_value="/usr/bin/ollama"), \
         patch("local_ai.ollama_client.subprocess.Popen") as mock_popen, \
         patch("local_ai.ollama_client.time.sleep"):
        assert client.ensure_running(wait_seconds=3) is True
        mock_popen.assert_called_once()


def test_ask_creates_goal_from_recordame_without_using_model(engine):
    """Bloque 9: 'recordame que...' crea un objetivo, sin gastar el modelo, y no interfiere con memoria."""
    assistant = LocalAssistant(engine=engine)
    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("Recordame que compre pan")

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"
    assert "compre pan" in result.answer

    pending = assistant.goal_manager.list_pending()
    assert len(pending) == 1
    assert pending[0].content == "compre pan"

    # No debe haberse guardado nada como memoria (es un objetivo, no un hecho).
    assert engine.get_all_memories() == []


def test_ask_goal_creation_and_update_full_cycle(engine):
    """Bloque 10: crear un objetivo con fecha relativa, y despues actualizarlo mencionandolo explicitamente."""
    assistant = LocalAssistant(engine=engine)

    with patch.object(OllamaClient, "generate") as mock_generate:
        r1 = assistant.ask("Recordame estudiar Linux mañana")
        assert mock_generate.assert_not_called() is None

    pending = assistant.goal_manager.list_pending()
    assert len(pending) == 1
    assert pending[0].content == "estudiar Linux"
    assert pending[0].due_at is not None

    r2 = assistant.ask("cambiar estudiar Linux para el viernes")
    assert "actualicé" in r2.answer

    updated = assistant.goal_manager.get_goal(pending[0].id)
    assert updated.due_at is not None

    # Ambiguo: pedir aclaracion en vez de adivinar.
    assistant.goal_manager.create_goal("estudiar Python")
    r3 = assistant.ask("cambiar estudiar para el lunes")
    assert "No estoy seguro" in r3.answer


def test_global_context_query_never_intercepted_by_partial_lexical_match(engine):
    """Bloque 11B: la razon de ser de este bloque. Con UNA sola memoria de
    proyecto guardada, una coincidencia lexica puntual existiria (score alto),
    pero la pregunta de vista global debe devolver TODAS las categorias
    relevantes desde el digest, no solo lo que matchearia por palabras clave."""
    assistant = LocalAssistant(engine=engine)
    engine.save_memory(content="Proyecto: OmniLocal", memory_type="hecho", importance=0.75)
    engine.save_memory(content="Proyecto: Fenix", memory_type="hecho", importance=0.75)

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("¿Qué proyectos tengo?")

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"
    assert "OmniLocal" in result.answer
    assert "Fenix" in result.answer  # las DOS, no solo la que hubiera matcheado por lexico


def test_ambiguous_global_phrasing_falls_through_to_normal_flow(engine):
    """Condicion de la aprobacion: '¿Que estoy haciendo?' no dispara el
    digest -- sigue el flujo normal (en este caso, sin memoria ni modelo,
    termina en 'sin_modelo', pero lo importante es que NO devuelve un
    listado inventado)."""
    assistant = LocalAssistant(engine=engine)
    result = assistant.ask("¿Qué estoy haciendo?")
    assert result.source != "memoria_local" or "pendiente" not in result.answer.lower()


def test_synthesis_query_without_model_returns_digest_directly(engine):
    """Bloque 11C: sin Ollama, degrada al listado plano del digest, no a un error."""
    assistant = LocalAssistant(engine=engine)
    engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)
    assistant.goal_manager.create_goal("Estudiar Linux")

    result = assistant.ask("Dame un resumen")

    assert result.source == "memoria_local"
    assert result.used_model is False
    assert "Marcelo" in result.answer
    assert "Estudiar Linux" in result.answer


def test_synthesis_query_with_model_uses_digest_as_context_and_system_prompt(engine):
    """Con modelo disponible: se le pasa el digest completo como contexto y el system prompt restrictivo."""
    from local_ai.assistant import _SYNTHESIS_SYSTEM_PROMPT

    assistant = LocalAssistant(engine=engine)
    engine.save_memory(content="Nombre: Marcelo", memory_type="hecho", importance=0.75)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Segun lo que se, tu nombre es Marcelo."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = assistant.ask("¿Qué sabés de mí?")

    assert result.source == "modelo_ia"
    assert captured["system"] == _SYNTHESIS_SYSTEM_PROMPT
    assert any("Marcelo" in c for c in captured["context_chunks"])


def test_direct_match_takes_priority_over_synthesis_query(engine):
    """Regresion: si hubiera coincidencia directa, la sintesis (Bloque 11C) ni se intenta."""
    assistant = LocalAssistant(engine=engine)
    assistant.remember("dame un resumen de esto: RedCasa123")  # contenido armado para matchear literal

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("dame un resumen de esto: RedCasa123")

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"


def test_project_switch_persists_and_is_readable(engine):
    """Bloque 16: activar un proyecto real, confirmar que persiste y se puede releer."""
    assistant = LocalAssistant(engine=engine)
    project_id = assistant.project_manager.create_project("OmniLocal", "/home/user/omnilocal")
    session_id = engine.db_manager.insert_chat_session("Charla")

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("Trabajemos en OmniLocal", session_id=session_id)

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"
    assert "OmniLocal" in result.answer

    session = engine.db_manager.get_chat_session(session_id)
    assert session["active_project_id"] == project_id


def test_project_switch_without_session_id_does_not_crash(engine):
    assistant = LocalAssistant(engine=engine)
    assistant.project_manager.create_project("OmniLocal", "/home/user/omnilocal")
    result = assistant.ask("Trabajemos en OmniLocal")  # sin session_id
    assert "sesión" in result.answer.lower()


def test_project_switch_ambiguous_asks_for_clarification(engine):
    assistant = LocalAssistant(engine=engine)
    assistant.project_manager.create_project("OmniLocal Core", "/a")
    assistant.project_manager.create_project("OmniLocal Mobile", "/b")
    session_id = engine.db_manager.insert_chat_session("Charla")

    result = assistant.ask("Trabajemos en OmniLocal", session_id=session_id)
    assert "no estoy seguro" in result.answer.lower()


def test_code_explanation_end_to_end_real_project(engine, tmp_path):
    """Bloque 17: proyecto real + Bloque 14/15/16 corridos, pedir explicacion de un archivo real."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    import json as json_module

    (tmp_path / "flashcards.py").write_text("class Flashcard:\n    pass\n\ndef load(): pass\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("App Diccionario", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )

    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en App Diccionario", session_id=session_id)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Este archivo define la clase Flashcard y una función load."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = assistant.ask("Explicame flashcards.py", session_id=session_id)

    assert result.source == "modelo_ia"
    assert "Flashcard" in result.answer
    assert captured["system"] is not None
    assert "opines" in captured["system"].lower() or "no opines" in captured["system"].lower()
    assert any("class Flashcard" in c for c in captured["context_chunks"])


def test_code_explanation_without_active_project(engine):
    assistant = LocalAssistant(engine=engine)
    session_id = engine.db_manager.insert_chat_session("Charla")
    result = assistant.ask("Explicame main.py", session_id=session_id)
    assert "activá un proyecto" in result.answer.lower()


def test_code_explanation_file_not_found(engine, tmp_path):
    from local_ai.project_scanner import scan_project_structure
    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("Vacio", scan_result.path)
    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en Vacio", session_id=session_id)

    result = assistant.ask("Explicame no_existe.py", session_id=session_id)
    assert "no estoy seguro" in result.answer.lower()


def test_code_review_end_to_end_uses_review_prompt_not_explain_prompt(engine, tmp_path):
    """Bloque 18: 'revisa X.py' usa el prompt de revision (pide opinar), no el de explicacion."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    from local_ai.code_reviewer import _REVIEW_SYSTEM_PROMPT
    import json as json_module

    (tmp_path / "flashcards.py").write_text("class Flashcard:\n    pass\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("App Diccionario", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )

    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en App Diccionario", session_id=session_id)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "El diseño parece razonable, pero podría separar la logica de persistencia."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = assistant.ask("Revisá flashcards.py", session_id=session_id)

    assert result.source == "modelo_ia"
    assert captured["system"] == _REVIEW_SYSTEM_PROMPT
    assert "no opines" not in captured["system"].lower()


def test_analizame_now_triggers_review_not_explanation(engine, tmp_path):
    """Confirmacion de la correccion del Bloque 18: 'analizame' ya no dispara el Bloque 17."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    from local_ai.code_reviewer import _REVIEW_SYSTEM_PROMPT
    import json as json_module

    (tmp_path / "main.py").write_text("x = 1\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("Proyecto", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )

    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en Proyecto", session_id=session_id)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "opinion"

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        assistant.ask("analizame main.py", session_id=session_id)

    assert captured["system"] == _REVIEW_SYSTEM_PROMPT


def test_search_content_end_to_end_real_project(engine, tmp_path):
    """Bloque 19: busqueda deterministica, cero modelo."""
    (tmp_path / "auth.py").write_text("def login(user, password):\n    pass\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = __import__("local_ai.project_scanner", fromlist=["scan_project_structure"]).scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("Proyecto", scan_result.path)
    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en Proyecto", session_id=session_id)

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("Buscá password", session_id=session_id)

    mock_generate.assert_not_called()
    assert result.source == "memoria_local"
    assert "auth.py" in result.answer


def test_import_relation_end_to_end_real_project(engine, tmp_path):
    """Bloque 19: relacion por imports, consulta estructural, cero modelo."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    import json as json_module

    (tmp_path / "auth.py").write_text("import os\nimport hashlib\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("Proyecto", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )
    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en Proyecto", session_id=session_id)

    with patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("¿Qué importa auth.py?", session_id=session_id)

    mock_generate.assert_not_called()
    assert "os" in result.answer
    assert "hashlib" in result.answer


def test_compare_files_end_to_end_uses_model(engine, tmp_path):
    """Bloque 19: comparar SI usa el modelo, a diferencia de busqueda/imports."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    from local_ai.code_comparator import _COMPARE_SYSTEM_PROMPT
    import json as json_module

    (tmp_path / "old_auth.py").write_text("def login(): pass\n")
    (tmp_path / "new_auth.py").write_text("def login_v2(): pass\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("Proyecto", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )
    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en Proyecto", session_id=session_id)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Ambos definen una funcion de login, la nueva tiene un nombre distinto."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = assistant.ask("Comparar old_auth.py y new_auth.py", session_id=session_id)

    assert result.source == "modelo_ia"
    assert captured["system"] == _COMPARE_SYSTEM_PROMPT
    assert any("login()" in c for c in captured["context_chunks"])
    assert any("login_v2()" in c for c in captured["context_chunks"])


def test_change_proposal_without_active_project_never_calls_model(engine):
    """Ajuste 2 de la aprobacion: sin proyecto activo, corta ANTES de tocar el modelo."""
    assistant = LocalAssistant(engine=engine)
    session_id = engine.db_manager.insert_chat_session("Charla")

    with patch.object(OllamaClient, "is_available") as mock_available, \
         patch.object(OllamaClient, "generate") as mock_generate:
        result = assistant.ask("Quiero agregar recuperación de contraseña", session_id=session_id)

    mock_available.assert_not_called()
    mock_generate.assert_not_called()
    assert result.answer == "Necesito que actives un proyecto primero."


def test_change_proposal_end_to_end_uses_full_project_structure(engine, tmp_path):
    """Bloque 20: el contexto enviado al modelo incluye TODOS los archivos, no uno solo."""
    from local_ai.project_scanner import scan_project_structure
    from local_ai.code_analyzer import scan_project_code
    from local_ai.change_proposer import _PROPOSAL_SYSTEM_PROMPT
    import json as json_module

    (tmp_path / "auth.py").write_text("class AuthManager:\n    pass\n")
    (tmp_path / "database.py").write_text("def connect(): pass\n")

    assistant = LocalAssistant(engine=engine)
    scan_result = scan_project_structure(str(tmp_path))
    project_id = assistant.project_manager.create_project("App Diccionario", scan_result.path)
    for fa in scan_project_code(str(tmp_path)):
        engine.db_manager.insert_project_file(
            project_id, fa.relative_path, fa.language,
            json_module.dumps(fa.classes), json_module.dumps(fa.functions), json_module.dumps(fa.imports),
            parse_error=fa.parse_error,
        )
    session_id = engine.db_manager.insert_chat_session("Charla")
    assistant.ask("Trabajemos en App Diccionario", session_id=session_id)

    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Podrías agregar un ResetToken en auth.py y una consulta en database.py."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = assistant.ask("Quiero agregar recuperación de contraseña", session_id=session_id)

    assert result.source == "modelo_ia"
    assert captured["system"] == _PROPOSAL_SYSTEM_PROMPT
    overview = captured["context_chunks"][0]
    assert "auth.py" in overview
    assert "database.py" in overview
    assert "AuthManager" in overview
    assert "connect" in overview
