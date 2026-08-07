from datetime import date, timedelta

from local_ai.goal_date_parser import parse_relative_date

MONDAY = date(2026, 8, 3)  # confirmado lunes


def test_hoy():
    result, cleaned = parse_relative_date("estudiar Linux hoy", reference_date=MONDAY)
    assert result == MONDAY
    assert "hoy" not in cleaned
    assert "estudiar Linux" in cleaned


def test_manana():
    result, cleaned = parse_relative_date("estudiar Linux mañana", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=1)
    assert "mañana" not in cleaned


def test_pasado_manana():
    result, cleaned = parse_relative_date("estudiar Linux pasado mañana", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=2)
    assert "pasado" not in cleaned and "mañana" not in cleaned


def test_en_n_dias():
    result, cleaned = parse_relative_date("estudiar Linux en 3 dias", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=3)
    assert "3" not in cleaned


def test_en_n_dias_con_tilde():
    result, _ = parse_relative_date("estudiar Linux en 5 días", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=5)


def test_no_date_found_returns_none_and_original_text():
    result, cleaned = parse_relative_date("estudiar Linux", reference_date=MONDAY)
    assert result is None
    assert cleaned == "estudiar Linux"


def test_weekday_same_day_means_next_week():
    """Regla acordada: 'el lunes' dicho un lunes -> el proximo lunes (+7), nunca hoy."""
    result, _ = parse_relative_date("estudiar Linux el lunes", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=7)


def test_weekday_next_occurrence_this_week():
    """'martes' dicho un lunes -> mañana (la proxima ocurrencia futura)."""
    result, _ = parse_relative_date("estudiar Linux el martes", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=1)


def test_weekday_far_in_the_week():
    result, cleaned = parse_relative_date("estudiar Linux el viernes", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=4)
    assert "viernes" not in cleaned


def test_weekday_without_el_prefix():
    result, _ = parse_relative_date("estudiar Linux domingo", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=6)


def test_pasado_manana_not_confused_with_manana():
    """'pasado mañana' no debe matchear como si fuera solo 'mañana'."""
    result, _ = parse_relative_date("algo pasado mañana", reference_date=MONDAY)
    assert result == MONDAY + timedelta(days=2)
