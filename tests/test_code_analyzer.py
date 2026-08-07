import inspect

import pytest

from local_ai.code_analyzer import analyze_python_file, scan_project_code, MAX_FILE_CHARS_FOR_ANALYSIS


SAMPLE_CODE = '''
import os
from typing import Optional

class Flashcard:
    """Una clase real, con un metodo adentro que NO debe extraerse."""
    def show(self):
        pass

class Deck:
    pass

def create_flashcard(word):
    return Flashcard()

async def load_deck():
    pass
'''


@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "flashcards.py"
    f.write_text(SAMPLE_CODE)
    return f


# ----------------------------------------------------------------
# analyze_python_file
# ----------------------------------------------------------------
def test_extracts_classes(sample_file):
    result = analyze_python_file(str(sample_file))
    assert set(result.classes) == {"Flashcard", "Deck"}


def test_extracts_module_level_functions_including_async(sample_file):
    result = analyze_python_file(str(sample_file))
    assert set(result.functions) == {"create_flashcard", "load_deck"}


def test_methods_inside_classes_are_excluded_by_design(sample_file):
    """Confirmacion explicita pedida en la aprobacion: 'show' (metodo de
    Flashcard) NO debe aparecer en functions -- es una decision de diseño,
    no un bug."""
    result = analyze_python_file(str(sample_file))
    assert "show" not in result.functions


def test_extracts_imports(sample_file):
    result = analyze_python_file(str(sample_file))
    assert "os" in result.imports
    assert "typing" in result.imports


def test_no_parse_error_on_valid_file(sample_file):
    result = analyze_python_file(str(sample_file))
    assert result.parse_error is None


def test_empty_file_returns_empty_lists(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    result = analyze_python_file(str(f))
    assert result.classes == []
    assert result.functions == []
    assert result.imports == []
    assert result.parse_error is None


def test_syntax_error_sets_parse_error_not_exception(tmp_path):
    f = tmp_path / "broken.py"
    f.write_text("def foo(:\n    pass")
    result = analyze_python_file(str(f))
    assert result.parse_error is not None
    assert "sintaxis" in result.parse_error.lower()


def test_unreadable_file_sets_parse_error_not_exception():
    result = analyze_python_file("/esta/ruta/no/existe.py")
    assert result.parse_error is not None


def test_huge_file_sets_parse_error_instead_of_analyzing(tmp_path):
    f = tmp_path / "huge.py"
    f.write_text("x = 1\n" * (MAX_FILE_CHARS_FOR_ANALYSIS // 5))
    result = analyze_python_file(str(f))
    assert result.parse_error is not None
    assert "grande" in result.parse_error.lower()


# ----------------------------------------------------------------
# scan_project_code
# ----------------------------------------------------------------
@pytest.fixture
def sample_project(tmp_path):
    (tmp_path / "main.py").write_text("def start(): pass")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "utils.py").write_text("class Helper: pass")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.py").write_text("class ShouldNotAppear: pass")
    (tmp_path / "README.md").write_text("no es python")
    return tmp_path


def test_scan_finds_python_files_only(sample_project):
    results = scan_project_code(str(sample_project))
    paths = {r.relative_path for r in results}
    assert "main.py" in paths
    assert any("utils.py" in p for p in paths)
    assert not any("README" in p for p in paths)


def test_scan_excludes_node_modules(sample_project):
    results = scan_project_code(str(sample_project))
    all_classes = [c for r in results for c in r.classes]
    assert "ShouldNotAppear" not in all_classes


def test_scan_nonexistent_project_returns_empty_list():
    assert scan_project_code("/no/existe/en/serio") == []


def test_scan_respects_max_files(sample_project):
    for i in range(10):
        (sample_project / f"module_{i}.py").write_text("x = 1")
    results = scan_project_code(str(sample_project), max_files=3)
    assert len(results) == 3


# ----------------------------------------------------------------
# Separacion estricta de Ollama (condicion de la aprobacion)
# ----------------------------------------------------------------
def test_code_analyzer_does_not_import_ollama():
    from local_ai import code_analyzer
    source = inspect.getsource(code_analyzer)
    assert "ollama" not in source.lower()
