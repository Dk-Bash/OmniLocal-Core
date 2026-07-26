import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine


def test_error_handling_invalid_memory_params():
    """
    Comprueba que el Core Engine maneje errores de validación de forma controlada
    (ej: importancia fuera de rango [0.0 - 1.0]) y no silencie errores inesperados.
    """
    engine = OmniLocalEngine()
    engine.start()

    # Importancia inválida (> 1.0) debe levantar ValueError con mensaje claro
    try:
        engine.save_memory("Contenido de prueba", "episodic", importance=1.5)
        assert False, "Debe lanzar ValueError por importancia fuera de rango."
    except ValueError as ve:
        assert "importance" in str(ve).lower() or "1.0" in str(ve) or "validation" in str(ve).lower()

    # Importancia inválida (< 0.0)
    try:
        engine.save_memory("Contenido de prueba", "episodic", importance=-0.5)
        assert False, "Debe lanzar ValueError por importancia negativa."
    except ValueError as ve:
        assert "importance" in str(ve).lower() or "0.0" in str(ve) or "validation" in str(ve).lower()


def test_error_handling_nonexistent_and_invalid_ids():
    """
    Comprueba que la búsqueda con ID inexistente o no válido (-1, 0, tipo no entero)
    se maneje limpiamente devolviendo None sin romper la aplicación.
    """
    engine = OmniLocalEngine()
    engine.start()

    # ID inexistente
    res = engine.get_memory(999999)
    assert res is None, "La búsqueda de un ID inexistente debe devolver None."

    # ID inválido negativo o cero
    res_neg = engine.get_memory(-5)
    assert res_neg is None, "La búsqueda con ID negativo debe devolver None."

    res_zero = engine.get_memory(0)
    assert res_zero is None, "La búsqueda con ID 0 debe devolver None."

    print("✅ test_error_handling.py: Manejo de errores controlado y verificado correctamente.")


if __name__ == "__main__":
    test_error_handling_invalid_memory_params()
    test_error_handling_nonexistent_and_invalid_ids()
