import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.logger import get_logger


def test_logger_creation_and_output():
    """
    Prueba unitaria para verificar la creación y funcionamiento del sistema de logging.
    """
    logger = get_logger("test_module")
    assert logger is not None, "get_logger debe devolver una instancia válida de Logger."
    assert isinstance(logger, logging.Logger), "El objeto devuelto debe ser logging.Logger."
    assert logger.name == "test_module", "El nombre del logger debe coincidir."

    # Probar niveles de log sin errores
    logger.debug("Mensaje de depuración de prueba")
    logger.info("Mensaje informativo de prueba")
    logger.warning("Mensaje de advertencia de prueba")
    logger.error("Mensaje de error de prueba")

    print("✅ test_logger.py: El sistema de logging se creó y emite mensajes correctamente.")


if __name__ == "__main__":
    test_logger_creation_and_output()
