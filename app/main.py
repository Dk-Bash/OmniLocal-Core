import os
import sys

# Asegurar que el directorio raíz del proyecto esté en el path de importación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine


def main():
    engine = OmniLocalEngine()
    engine.start()
    print("OmniLocal Core v0.1 iniciado correctamente")


if __name__ == "__main__":
    main()
