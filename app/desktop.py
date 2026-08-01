"""
Lanzador de escritorio de OmniLocal-Core.

Levanta el backend local (FastAPI) en un hilo de fondo y abre la interfaz
en una ventana nativa (no un navegador) usando pywebview. Todo corre en
127.0.0.1: nada de esto sale a la red.

Uso:
    python app/desktop.py
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import uvicorn
import webview

from app.logger import get_logger

logger = get_logger(__name__)

HOST = "127.0.0.1"
PORT = int(os.getenv("OMNILOCAL_UI_PORT", "8756"))
URL = f"http://{HOST}:{PORT}"


def _run_server() -> None:
    from webapp.server import app  # import diferido: crea el motor recién acá

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def _wait_for_server(timeout: int = 30) -> bool:
    for _ in range(timeout * 2):
        try:
            resp = requests.get(f"{URL}/api/health", timeout=2)
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def main() -> None:
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    if not _wait_for_server():
        logger.error("El backend local no respondió a tiempo. Revisá que el puerto %s esté libre.", PORT)
        print(f"No se pudo iniciar el servidor local en {URL}. Cerrando.")
        return

    webview.create_window("OmniLocal-Core", URL, width=1280, height=800, min_size=(900, 600))
    webview.start()


if __name__ == "__main__":
    main()
