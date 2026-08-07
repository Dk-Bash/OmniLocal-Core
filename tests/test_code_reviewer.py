import inspect

from local_ai.code_reviewer import detect_review_request, _REVIEW_SYSTEM_PROMPT


# ----------------------------------------------------------------
# detect_review_request
# ----------------------------------------------------------------
def test_detects_revisa():
    assert detect_review_request("Revisá flashcards.py") == "flashcards.py"


def test_detects_analiza_now_belongs_here():
    assert detect_review_request("analizame main.py") == "main.py"


def test_detects_esta_bien_disenado():
    assert detect_review_request("¿Está bien diseñado authentication.py?") == "authentication.py"


def test_detects_esta_bien_plain():
    assert detect_review_request("¿Está bien utils.py?") == "utils.py"


def test_detects_que_opinas_de():
    assert detect_review_request("¿Qué opinás de main.py?") == "main.py"


def test_detects_hay_problemas_en():
    assert detect_review_request("¿Hay problemas en flashcards.py?") == "flashcards.py"


def test_ignores_generic_requests_without_filename():
    assert detect_review_request("revisá esto") is None
    assert detect_review_request("está todo bien?") is None


def test_ignores_empty_text():
    assert detect_review_request("") is None


# ----------------------------------------------------------------
# El prompt debe pedir opinar (a diferencia del Bloque 17) y calibrar expectativas
# ----------------------------------------------------------------
def test_review_prompt_asks_for_opinion_unlike_block_17():
    assert "no opines" not in _REVIEW_SYSTEM_PROMPT.lower()
    assert "evalu" in _REVIEW_SYSTEM_PROMPT.lower() or "opinión" in _REVIEW_SYSTEM_PROMPT.lower()


def test_review_prompt_calibrates_expectations():
    assert "modelo chico" in _REVIEW_SYSTEM_PROMPT.lower() or "no un reemplazo" in _REVIEW_SYSTEM_PROMPT.lower()


def test_review_prompt_forbids_applying_changes():
    assert "no los apliques" in _REVIEW_SYSTEM_PROMPT.lower() or "no modificás nada" in _REVIEW_SYSTEM_PROMPT.lower()


# ----------------------------------------------------------------
# Test espejo del Bloque 17: solo lectura, cero escritura/ejecucion
# ----------------------------------------------------------------
def test_code_reviewer_never_writes_or_executes():
    from local_ai import code_reviewer
    source = inspect.getsource(code_reviewer)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "os.remove" not in source
    assert '"w")' not in source
    assert "'w')" not in source
