import inspect
import json

from local_ai.change_proposer import (
    detect_change_proposal_request,
    build_project_overview,
    _PROPOSAL_SYSTEM_PROMPT,
)


class FakeProject:
    def __init__(self, name, technologies=None):
        self.name = name
        self.technologies = technologies


# ----------------------------------------------------------------
# detect_change_proposal_request
# ----------------------------------------------------------------
def test_detects_quiero_agregar():
    assert detect_change_proposal_request("Quiero agregar recuperación de contraseña") == "recuperación de contraseña"


def test_detects_necesito_agregar():
    assert detect_change_proposal_request("necesito agregar autenticación con Google") == "autenticación con Google"


def test_detects_como_implemento():
    assert detect_change_proposal_request("¿Cómo implemento notificaciones push?") == "notificaciones push"


def test_detects_proponeme_cambios():
    assert detect_change_proposal_request("proponeme cambios para modo oscuro") == "modo oscuro"


def test_ignores_unrelated_text():
    assert detect_change_proposal_request("¿Cómo me llamo?") is None
    assert detect_change_proposal_request("hola, como estas") is None


def test_ignores_empty_text():
    assert detect_change_proposal_request("") is None


# ----------------------------------------------------------------
# build_project_overview
# ----------------------------------------------------------------
def test_overview_includes_all_files_not_just_one():
    project = FakeProject("App Diccionario", technologies="Python, SQLite")
    project_files = [
        {"relative_path": "auth.py", "classes": json.dumps(["AuthManager"]), "functions": json.dumps(["login"]), "imports": json.dumps(["hashlib"])},
        {"relative_path": "database.py", "classes": "[]", "functions": json.dumps(["connect"]), "imports": json.dumps(["sqlite3"])},
    ]
    overview = build_project_overview(project, project_files)
    assert "auth.py" in overview
    assert "database.py" in overview
    assert "AuthManager" in overview
    assert "connect" in overview
    assert "App Diccionario" in overview
    assert "Python, SQLite" in overview


def test_overview_handles_malformed_json_gracefully():
    project = FakeProject("Proyecto")
    project_files = [{"relative_path": "broken.py", "classes": "not json", "functions": "[]", "imports": "[]"}]
    overview = build_project_overview(project, project_files)
    assert "broken.py" in overview  # no debe lanzar excepcion


# ----------------------------------------------------------------
# Prompt -- lenguaje sugerente, no prescriptivo (Ajuste 1 de la aprobacion)
# ----------------------------------------------------------------
def test_prompt_uses_suggestive_language_not_prescriptive():
    assert "podrían estar relacionados" in _PROPOSAL_SYSTEM_PROMPT
    assert "hay que modificar" not in _PROPOSAL_SYSTEM_PROMPT.lower()


def test_prompt_forbids_diffs_and_application():
    assert "no generes un diff" in _PROPOSAL_SYSTEM_PROMPT.lower()
    assert "no apliques nada" in _PROPOSAL_SYSTEM_PROMPT.lower()


def test_prompt_calibrates_expectations_about_structure_only():
    assert "no en el código real" in _PROPOSAL_SYSTEM_PROMPT.lower()


# ----------------------------------------------------------------
# Test espejo: solo lectura, cero escritura/ejecucion
# ----------------------------------------------------------------
def test_change_proposer_never_writes_or_executes():
    from local_ai import change_proposer
    source = inspect.getsource(change_proposer)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert '"w")' not in source
