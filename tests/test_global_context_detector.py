from local_ai.global_context_detector import detect_global_context_query, format_section_answer, GlobalContextQuery


# ----------------------------------------------------------------
# Detección
# ----------------------------------------------------------------
def test_detects_pendientes():
    result = detect_global_context_query("¿Qué tengo pendiente?")
    assert result is not None
    assert result.section == "objetivos_pendientes"


def test_detects_mis_pendientes_variant():
    assert detect_global_context_query("mostrame mis pendientes").section == "objetivos_pendientes"


def test_detects_proyectos_plural():
    result = detect_global_context_query("¿Qué proyectos tengo?")
    assert result is not None
    assert result.section == "proyecto"


def test_detects_mis_proyectos_variant():
    assert detect_global_context_query("mis proyectos").section == "proyecto"


def test_detects_preferencias():
    result = detect_global_context_query("¿Qué preferencias tengo?")
    assert result.section == "preferencia"


def test_detects_ocupacion():
    result = detect_global_context_query("¿En qué trabajo?")
    assert result.section == "ocupacion"


# ----------------------------------------------------------------
# Regla de ambigüedad (condición de la aprobación): nunca adivinar
# ----------------------------------------------------------------
def test_ambiguous_phrasing_does_not_trigger():
    """'¿Qué estoy haciendo?' es parecido pero no matchea ningún patrón conocido -> None."""
    assert detect_global_context_query("¿Qué estoy haciendo?") is None


def test_unrelated_question_does_not_trigger():
    assert detect_global_context_query("¿Cómo me llamo?") is None


def test_singular_project_question_does_not_trigger():
    """'¿Cuál es mi proyecto?' (singular) no debe activar la vista global -- es intencionalmente estricto."""
    assert detect_global_context_query("¿Cuál es mi proyecto?") is None


def test_empty_text():
    assert detect_global_context_query("") is None
    assert detect_global_context_query("   ") is None


# ----------------------------------------------------------------
# Formato de respuesta
# ----------------------------------------------------------------
def test_format_pendientes_with_items():
    digest = {"objetivos_pendientes": ["Estudiar Linux", "Comprar pan"], "hechos_por_categoria": {}}
    answer = format_section_answer(digest, GlobalContextQuery(section="objetivos_pendientes"))
    assert "2 pendientes" in answer
    assert "Estudiar Linux" in answer
    assert "Comprar pan" in answer


def test_format_pendientes_singular():
    digest = {"objetivos_pendientes": ["Estudiar Linux"], "hechos_por_categoria": {}}
    answer = format_section_answer(digest, GlobalContextQuery(section="objetivos_pendientes"))
    assert "1 pendiente:" in answer
    assert "pendientes" not in answer  # sin la "s"


def test_format_empty_section():
    digest = {"objetivos_pendientes": [], "hechos_por_categoria": {}}
    answer = format_section_answer(digest, GlobalContextQuery(section="objetivos_pendientes"))
    assert "No tenés" in answer


def test_format_proyectos_strips_category_prefix():
    digest = {"objetivos_pendientes": [], "hechos_por_categoria": {"proyecto": ["Proyecto: OmniLocal", "Proyecto: Fenix"]}}
    answer = format_section_answer(digest, GlobalContextQuery(section="proyecto"))
    assert "OmniLocal" in answer
    assert "Fenix" in answer
    assert "Proyecto:" not in answer  # no repite el prefijo, ya lo dice el label
