import inspect

from local_ai.code_comparator import detect_compare_request, _COMPARE_SYSTEM_PROMPT


def test_detects_comparar_y():
    assert detect_compare_request("Comparar auth.py y login.py") == ("auth.py", "login.py")


def test_detects_compara_con():
    assert detect_compare_request("compará main.py con app.py") == ("main.py", "app.py")


def test_detects_diferencia_entre():
    assert detect_compare_request("¿Diferencia entre old.py y new.py?") == ("old.py", "new.py")


def test_ignores_single_file_mention():
    assert detect_compare_request("comparar main.py") is None


def test_ignores_unrelated_text():
    assert detect_compare_request("¿cómo estás?") is None


def test_ignores_empty_text():
    assert detect_compare_request("") is None


def test_prompt_forbids_modification():
    assert "no modificás" in _COMPARE_SYSTEM_PROMPT.lower()


def test_prompt_calibrates_expectations():
    assert "modelo chico" in _COMPARE_SYSTEM_PROMPT.lower()


def test_code_comparator_never_writes_or_executes():
    from local_ai import code_comparator
    source = inspect.getsource(code_comparator)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert '"w")' not in source
