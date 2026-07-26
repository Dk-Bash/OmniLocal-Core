from app.config import PROJECT_NAME, VERSION


class OmniLocalEngine:
    """
    Clase núcleo inicial para OmniLocal-Core.
    Gestiona la inicialización y el estado básico del motor local.
    """

    def __init__(self):
        self.name = PROJECT_NAME
        self.version = VERSION
        self.is_running = False

    def start(self) -> bool:
        """Inicia el motor de OmniLocal-Core."""
        self.is_running = True
        return True

    def status(self) -> dict:
        """Devuelve el estado actual del motor."""
        return {
            "name": self.name,
            "version": self.version,
            "running": self.is_running,
            "status": "ready" if self.is_running else "stopped",
        }
