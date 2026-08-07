from local_ai.synthesis_detector import detect_synthesis_query


def test_detects_dame_un_resumen():
    assert detect_synthesis_query("Dame un resumen") is True


def test_detects_que_sabes_de_mi():
    assert detect_synthesis_query("¿Qué sabés de mí?") is True


def test_detects_cosas_importantes_que_sabes():
    assert detect_synthesis_query("¿Cuáles son las cosas importantes que sabés de mí?") is True


def test_detects_situacion_actual():
    assert detect_synthesis_query("¿Cuál es mi situación actual?") is True


def test_detects_contame_mi_situacion():
    assert detect_synthesis_query("Contame mi situación") is True


def test_does_not_overlap_with_block_11b_ocupacion():
    """'En que trabajo' es de 11B (ocupacion), no debe matchear acá -- sin solapamiento."""
    assert detect_synthesis_query("¿En qué trabajo?") is False
    assert detect_synthesis_query("¿En qué estoy trabajando?") is False


def test_ambiguous_phrasing_does_not_trigger():
    assert detect_synthesis_query("¿Qué estoy haciendo?") is False


def test_unrelated_question_does_not_trigger():
    assert detect_synthesis_query("¿Cómo me llamo?") is False


def test_empty_text():
    assert detect_synthesis_query("") is False
    assert detect_synthesis_query("   ") is False
