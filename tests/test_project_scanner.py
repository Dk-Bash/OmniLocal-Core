import os

import pytest

from local_ai.project_scanner import scan_project_structure, detect_technologies


@pytest.fixture
def sample_project(tmp_path):
    (tmp_path / "main.py").write_text("print('hola')")
    (tmp_path / "requirements.txt").write_text("pydantic\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "utils.py").write_text("def f(): pass")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("// deberia ignorarse")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
    return tmp_path


def test_scan_finds_real_files(sample_project):
    result = scan_project_structure(str(sample_project))
    assert "main.py" in result.structure_summary
    assert os.path.join("src", "utils.py") in result.structure_summary
    assert result.entries_found >= 3


def test_scan_excludes_node_modules_and_git(sample_project):
    result = scan_project_structure(str(sample_project))
    assert "junk.js" not in result.structure_summary
    assert "HEAD" not in result.structure_summary


def test_scan_detects_python(sample_project):
    result = scan_project_structure(str(sample_project))
    assert "Python" in result.technologies


def test_scan_nonexistent_path_returns_empty_result():
    result = scan_project_structure("/esta/ruta/no/existe/en/serio")
    assert result.structure_summary == ""
    assert result.entries_found == 0


def test_scan_empty_folder(tmp_path):
    result = scan_project_structure(str(tmp_path))
    assert "vacía" in result.structure_summary
    assert result.technologies is None


def test_scan_truncates_large_projects(tmp_path):
    for i in range(350):
        (tmp_path / f"file_{i}.txt").write_text("x")
    result = scan_project_structure(str(tmp_path), max_entries=300)
    assert result.truncated is True
    assert result.entries_found == 350
    assert "más, no listados" in result.structure_summary


# ----------------------------------------------------------------
# detect_technologies
# ----------------------------------------------------------------
def test_detects_python_by_requirements():
    assert detect_technologies(["requirements.txt", "main.py"]) == "Python"


def test_detects_node_by_package_json():
    assert detect_technologies(["package.json", "index.js"]) == "Node.js/JavaScript"


def test_detects_typescript_over_generic_js():
    result = detect_technologies(["tsconfig.json", "index.ts"])
    assert "TypeScript" in result
    assert "Node.js/JavaScript" not in result


def test_detects_multiple_technologies():
    result = detect_technologies(["requirements.txt", "Dockerfile", "main.py"])
    assert "Python" in result
    assert "Docker" in result


def test_no_markers_returns_none():
    assert detect_technologies(["README.md", "notes.txt"]) is None


# ----------------------------------------------------------------
# read_readme
# ----------------------------------------------------------------
def test_read_readme_finds_readme_md(tmp_path):
    from local_ai.project_scanner import read_readme
    (tmp_path / "README.md").write_text("Este proyecto hace X.")
    content = read_readme(str(tmp_path))
    assert content == "Este proyecto hace X."


def test_read_readme_returns_none_without_readme(tmp_path):
    from local_ai.project_scanner import read_readme
    assert read_readme(str(tmp_path)) is None


# ----------------------------------------------------------------
# generate_status_summary -- bajo demanda, degrada sin modelo
# ----------------------------------------------------------------
def test_generate_status_summary_without_model_returns_none():
    from unittest.mock import patch
    from local_ai.ollama_client import OllamaClient
    from local_ai.project_scanner import generate_status_summary

    client = OllamaClient()
    with patch.object(OllamaClient, "is_available", return_value=False):
        result = generate_status_summary("main.py\nutils.py", client)
    assert result is None


def test_generate_status_summary_with_model_uses_structure_and_readme():
    from unittest.mock import patch
    from local_ai.ollama_client import OllamaClient
    from local_ai.project_scanner import generate_status_summary

    client = OllamaClient()
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Este proyecto es una app de diccionario para estudiar idiomas."

    with patch.object(OllamaClient, "is_available", return_value=True), \
         patch.object(OllamaClient, "generate", side_effect=fake_generate):
        result = generate_status_summary("main.py\nflashcards.py", client, readme_content="App para estudiar idiomas")

    assert "diccionario" in result
    assert "main.py" in captured["context_chunks"][0]
    assert "estudiar idiomas" in captured["context_chunks"][1]
