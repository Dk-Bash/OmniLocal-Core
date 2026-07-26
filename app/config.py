import os

# Configuración básica para OmniLocal-Core
PROJECT_NAME = "OmniLocal-Core"
VERSION = "0.1.0"

# Rutas principales del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
TESTS_DIR = os.path.join(BASE_DIR, "tests")
