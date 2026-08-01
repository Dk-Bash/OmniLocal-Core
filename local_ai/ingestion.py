"""
Ingestión de fuentes locales.

Permite registrar una carpeta del disco (por ejemplo tus notas, un vault de
Obsidian, la carpeta de un proyecto) para que su contenido de texto quede
disponible como conocimiento consultable por el asistente. Todo el trabajo
pasa por disco local: no se sube ni se descarga nada de ningún lado.
"""
import os
from dataclasses import dataclass
from typing import List

from app.core.engine import OmniLocalEngine
from app.logger import get_logger

logger = get_logger(__name__)

# Extensiones de texto plano que sabemos leer de forma segura.
SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".rst"}

# Tamaño máximo de fragmento guardado por archivo, para no inflar la memoria
# con archivos enormes de una sola vez.
MAX_CHARS_PER_FILE = 4000


@dataclass
class IngestionResult:
    path: str
    files_found: int
    files_indexed: int
    errors: List[str]


class SourceIngestor:
    """Escanea una carpeta local y vuelca su contenido de texto al conocimiento del sistema."""

    def __init__(self, engine: OmniLocalEngine):
        self.engine = engine

    def ingest_path(self, path: str) -> IngestionResult:
        path = os.path.abspath(os.path.expanduser(path))
        errors: List[str] = []

        if not os.path.exists(path):
            return IngestionResult(path=path, files_found=0, files_indexed=0, errors=[f"La ruta no existe: {path}"])

        files_found = 0
        files_indexed = 0

        targets = [path] if os.path.isfile(path) else self._walk_files(path)

        for file_path in targets:
            files_found += 1
            try:
                content = self._read_text_file(file_path)
                if not content.strip():
                    continue
                name = os.path.basename(file_path)
                self.engine.db_manager.insert_knowledge_node(
                    name=name,
                    node_type="documento_local",
                    description=content[:MAX_CHARS_PER_FILE],
                )
                files_indexed += 1
            except Exception as exc:  # un archivo con error no debe frenar el resto
                logger.warning(f"No se pudo indexar {file_path}: {exc}")
                errors.append(f"{file_path}: {exc}")

        self.engine.db_manager.insert_source(path)
        self.engine.db_manager.update_source_index_stats(path, files_indexed)

        return IngestionResult(path=path, files_found=files_found, files_indexed=files_indexed, errors=errors)

    @staticmethod
    def _walk_files(root: str) -> List[str]:
        found = []
        for dirpath, _dirnames, filenames in os.walk(root):
            # Ignorar carpetas ocultas y de control de versiones.
            if any(part.startswith(".") for part in dirpath.split(os.sep)):
                continue
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    found.append(os.path.join(dirpath, filename))
        return found

    @staticmethod
    def _read_text_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
