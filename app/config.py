import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuración básica para OmniLocal-Core
PROJECT_NAME = "OmniLocal-Core"
VERSION = "0.1.0"

# Entorno y Logging (Módulo 6)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rutas principales del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
TESTS_DIR = os.path.join(BASE_DIR, "tests")

# Ruta de la base de datos SQLite
DATABASE_PATH = os.path.join(DATA_DIR, "omnilocal.db")

# Configuración del motor de IA local (Ollama). Corre 100% en la máquina del
# usuario, sin conexión a servicios externos ni consumo de créditos/cuota.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
# Modelo de embeddings (Bloque 4A) -- separado del modelo de lenguaje.
# nomic-embed-text: ~274MB, liviano y suficiente para esta escala.
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
