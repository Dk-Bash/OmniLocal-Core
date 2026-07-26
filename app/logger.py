import logging
import sys
from app.config import LOG_LEVEL, ENVIRONMENT


def get_logger(name: str = "omnilocal") -> logging.Logger:
    """
    Crea y retorna un logger configurado con nivel y formato uniforme para OmniLocal-Core.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
