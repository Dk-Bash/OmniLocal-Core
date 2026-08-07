import inspect
import json

import pytest

from local_ai.code_explainer import (
    detect_explain_request,
    find_matching_project_file,
    read_file_content,
    build_explanation_context,
    MAX_FILE_CHARS_FOR_EXPLANATION,
)


# ----------------------------------------------------------------
# detect_explain_request
# ----------------------------------------------------------------
def test_detects_explicame():
    assert detect_explain_request("Explicame authentication.py") == "authentication.py"


def test_detects_explica_el_archivo():
    assert detect_explain_request("explicá el archivo utils.py") == "utils.py"


def test_detects_que_hace():
    assert detect_explain_request("¿Qué hace main.py?") == "main.py"


def test_analizame_no_longer_triggers_explanation():
    """Bloque 18: 'analizame X' se movio del Bloque 17 (explicacion) al
    Bloque 18 (revision/opinion), donde encaja semanticamente mejor."""
    assert detect_explain_request("analizame flashcards.py") is None


def test_ignores_generic_requests_without_filename():
    assert detect_explain_request("explicame esto") is None
    assert detect_explain_request("qué hace este proyecto") is None


def test_ignores_empty_text():
    assert detect_explain_request("") is None


# ----------------------------------------------------------------
# find_matching_project_file
# ----------------------------------------------------------------
def test_finds_exact_basename_match():
    files = [{"relative_path": "src/auth/authentication.py"}, {"relative_path": "main.py"}]
    match = find_matching_project_file(files, "authentication.py")
    assert match["relative_path"] == "src/auth/authentication.py"


def test_no_match_returns_none():
    files = [{"relative_path": "main.py"}]
    assert find_matching_project_file(files, "no_existe.py") is None


def test_ambiguous_same_basename_in_different_folders_returns_none():
    files = [{"relative_path": "src/utils.py"}, {"relative_path": "tests/utils.py"}]
    assert find_matching_project_file(files, "utils.py") is None


def test_empty_filename_returns_none():
    files = [{"relative_path": "main.py"}]
    assert find_matching_project_file(files, "") is None


# ----------------------------------------------------------------
# read_file_content
# ----------------------------------------------------------------
def test_reads_real_file(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("print('hola')")
    result = read_file_content(str(f))
    assert result.content == "print('hola')"
    assert result.truncated is False
    assert result.error is None


def test_nonexistent_file_returns_error_not_exception():
    result = read_file_content("/no/existe/en/serio.py")
    assert result.content is None
    assert result.error is not None


def test_truncates_large_file(tmp_path):
    f = tmp_path / "huge.py"
    f.write_text("x = 1\n" * MAX_FILE_CHARS_FOR_EXPLANATION)
    result = read_file_content(str(f), max_chars=100)
    assert result.truncated is True
    assert len(result.content) == 100


# ----------------------------------------------------------------
# build_explanation_context
# ----------------------------------------------------------------
def test_build_context_includes_structure_and_content():
    project_file = {
        "relative_path": "main.py",
        "classes": json.dumps(["App"]),
        "functions": json.dumps(["start"]),
        "imports": json.dumps(["os"]),
    }
    context = build_explanation_context(project_file, "print('hola')", truncated=False)
    assert "App" in context[0]
    assert "start" in context[0]
    assert "print('hola')" in context[1]
    assert "recortado" not in context[1]


def test_build_context_notes_truncation():
    project_file = {"relative_path": "main.py", "classes": "[]", "functions": "[]", "imports": "[]"}
    context = build_explanation_context(project_file, "contenido parcial", truncated=True)
    assert "recortado" in context[1]


# ----------------------------------------------------------------
# Test espejo del Bloque 15: solo lectura, cero escritura/ejecucion
# ----------------------------------------------------------------
def test_code_explainer_never_writes_or_executes():
    from local_ai import code_explainer
    source = inspect.getsource(code_explainer)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "os.remove" not in source
    assert '"w")' not in source
    assert "'w')" not in source
    assert ", \"w\"" not in source
