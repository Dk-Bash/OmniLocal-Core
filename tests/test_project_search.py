import inspect
import json

import pytest

from local_ai.project_search import (
    search_project_content,
    find_files_importing,
    get_file_imports,
    is_probably_binary,
)


@pytest.fixture
def sample_project(tmp_path):
    (tmp_path / "auth.py").write_text("def login(user, password):\n    check(password)\n")
    (tmp_path / "database.py").write_text("PASSWORD_FIELD = 'hash'\n")
    (tmp_path / "README.md").write_text("Nunca guardes el password en texto plano.")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "leak.js").write_text("password = 'secret'")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\x00\x00\x00fake")
    return tmp_path


# ----------------------------------------------------------------
# is_probably_binary
# ----------------------------------------------------------------
def test_detects_binary_by_null_byte(sample_project):
    assert is_probably_binary(str(sample_project / "image.png")) is True


def test_text_file_is_not_binary(sample_project):
    assert is_probably_binary(str(sample_project / "auth.py")) is False


def test_nonexistent_file_treated_as_binary():
    assert is_probably_binary("/no/existe/en/serio") is True


# ----------------------------------------------------------------
# search_project_content
# ----------------------------------------------------------------
def test_finds_literal_matches_across_extensions(sample_project):
    matches = search_project_content(str(sample_project), "password")
    paths = {m.relative_path for m in matches}
    assert "auth.py" in paths
    assert "database.py" in paths
    assert "README.md" in paths


def test_search_is_case_insensitive(sample_project):
    matches = search_project_content(str(sample_project), "PASSWORD")
    assert len(matches) > 0


def test_excludes_node_modules(sample_project):
    matches = search_project_content(str(sample_project), "password")
    assert not any("leak.js" in m.relative_path for m in matches)


def test_skips_binary_files(sample_project):
    matches = search_project_content(str(sample_project), "PNG")
    assert matches == []  # el contenido esta en un binario, no debe intentar leerlo como texto


def test_no_matches_returns_empty_list(sample_project):
    assert search_project_content(str(sample_project), "esto_no_existe_en_ningun_lado") == []


def test_empty_term_returns_empty_list(sample_project):
    assert search_project_content(str(sample_project), "") == []


def test_nonexistent_project_returns_empty_list():
    assert search_project_content("/no/existe/en/serio", "password") == []


def test_respects_max_matches(sample_project):
    for i in range(30):
        (sample_project / f"file_{i}.py").write_text("token = 'x'\n")
    matches = search_project_content(str(sample_project), "token", max_matches=5)
    assert len(matches) == 5


def test_this_is_literal_matching_not_semantic(sample_project):
    """Confirmacion de la decision de la auditoria: sin sinonimos, solo texto literal."""
    (sample_project / "creds.py").write_text("secret_key = 'abc'")  # no dice "password"
    matches = search_project_content(str(sample_project), "password")
    assert not any("creds.py" in m.relative_path for m in matches)


# ----------------------------------------------------------------
# find_files_importing / get_file_imports
# ----------------------------------------------------------------
def _pf(relative_path, imports):
    return {"relative_path": relative_path, "imports": json.dumps(imports)}


def test_find_files_importing_exact_module():
    project_files = [_pf("auth.py", ["os", "hashlib"]), _pf("main.py", ["auth"])]
    result = find_files_importing(project_files, "os")
    assert len(result) == 1
    assert result[0]["relative_path"] == "auth.py"


def test_find_files_importing_submodule():
    project_files = [_pf("main.py", ["local_ai.assistant"])]
    result = find_files_importing(project_files, "local_ai")
    assert len(result) == 1


def test_find_files_importing_no_match():
    project_files = [_pf("auth.py", ["os"])]
    assert find_files_importing(project_files, "requests") == []


def test_find_files_importing_empty_module_name():
    project_files = [_pf("auth.py", ["os"])]
    assert find_files_importing(project_files, "") == []


def test_get_file_imports_found():
    project_files = [_pf("auth.py", ["os", "hashlib"])]
    assert get_file_imports(project_files, "auth.py") == ["os", "hashlib"]


def test_get_file_imports_not_found():
    project_files = [_pf("auth.py", ["os"])]
    assert get_file_imports(project_files, "no_existe.py") is None


def test_get_file_imports_handles_malformed_json():
    project_files = [{"relative_path": "broken.py", "imports": "not json"}]
    assert get_file_imports(project_files, "broken.py") == []


# ----------------------------------------------------------------
# Test espejo: solo lectura, cero escritura/ejecucion
# ----------------------------------------------------------------
def test_project_search_never_writes_or_executes():
    from local_ai import project_search
    source = inspect.getsource(project_search)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "os.remove" not in source
    assert '"w")' not in source


# ----------------------------------------------------------------
# detect_search_request
# ----------------------------------------------------------------
from local_ai.project_search import detect_search_request, detect_import_relation_request


def test_detects_busca():
    """Nota: con frases mas largas, el termino extraido incluye todo lo que
    sigue al patron -- limitacion honesta de reglas simples, no un bug.
    Frases mas directas ('busca login') dan un termino mas limpio."""
    assert detect_search_request("Buscá login") == "login"


def test_detects_donde_esta_implementado():
    assert detect_search_request("¿Dónde está implementado el login?") == "el login"


def test_detects_encontrame():
    assert detect_search_request("encontrame password") == "password"


def test_search_ignores_empty():
    assert detect_search_request("") is None


# ----------------------------------------------------------------
# detect_import_relation_request
# ----------------------------------------------------------------
def test_detects_who_imports():
    result = detect_import_relation_request("¿Qué archivos importan auth?")
    assert result == ("who_imports", "auth")


def test_detects_quien_importa():
    result = detect_import_relation_request("¿Quién importa database?")
    assert result == ("who_imports", "database")


def test_detects_what_imports():
    result = detect_import_relation_request("¿Qué importa main.py?")
    assert result == ("what_imports", "main.py")


def test_import_relation_ignores_unrelated_text():
    assert detect_import_relation_request("¿cómo estás?") is None
