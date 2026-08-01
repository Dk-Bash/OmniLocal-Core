"""
Cliente para el motor de IA local (Ollama).

OmniLocal-Core no llama a ninguna IA externa ni servicio en la nube: este
cliente habla exclusivamente con un servidor de Ollama corriendo en la propia
máquina del usuario (por defecto http://localhost:11434). Si Ollama no está
instalado o el modelo no está disponible, el asistente sigue funcionando en
modo "solo memoria" (ver local_ai/assistant.py).
"""
import json
import os
import shutil
import subprocess
import time
from typing import List, Optional

import requests

from app.config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from app.logger import get_logger

logger = get_logger(__name__)


class OllamaUnavailableError(Exception):
    """Se lanza cuando no se puede contactar al servidor local de Ollama."""


class OllamaClient:
    """
    Cliente mínimo y sin dependencias pesadas para la API local de Ollama.
    Todas las solicitudes van a 127.0.0.1 / localhost: no hay tráfico externo.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.host = (host or OLLAMA_HOST).rstrip("/")
        self.model = model or OLLAMA_MODEL
        self.timeout = timeout or OLLAMA_TIMEOUT_SECONDS

    def is_available(self) -> bool:
        """Verifica si el servidor de Ollama está corriendo localmente."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def ensure_running(self, wait_seconds: int = 6) -> bool:
        """
        Si Ollama ya está corriendo, no hace nada. Si está instalado pero
        apagado, lo inicia solo en segundo plano (equivalente a que el
        usuario corra `ollama serve` a mano) y espera a que responda.
        Si no está instalado, devuelve False sin intentar nada más.
        """
        if self.is_available():
            return True

        if not shutil.which("ollama"):
            return False

        try:
            popen_kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if os.name == "nt":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(["ollama", "serve"], **popen_kwargs)
        except OSError as exc:
            logger.warning(f"No se pudo iniciar Ollama automáticamente: {exc}")
            return False

        for _ in range(wait_seconds):
            time.sleep(1)
            if self.is_available():
                return True
        return False

    def has_model(self) -> bool:
        """Verifica si el modelo configurado ya fue descargado con `ollama pull`."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            if resp.status_code != 200:
                return False
            data = resp.json()
            names = [m.get("name", "") for m in data.get("models", [])]
            return any(n == self.model or n.startswith(self.model.split(":")[0]) for n in names)
        except requests.exceptions.RequestException:
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        context_chunks: Optional[List[str]] = None,
    ) -> str:
        """
        Genera una respuesta con el modelo local. Lanza OllamaUnavailableError
        si el servidor no responde (el llamador decide cómo degradar).
        """
        full_prompt = prompt
        if context_chunks:
            joined = "\n".join(f"- {c}" for c in context_chunks if c)
            full_prompt = (
                "Contexto conocido (memoria local del sistema):\n"
                f"{joined}\n\n"
                f"Pregunta del usuario: {prompt}\n\n"
                "Respondé usando el contexto si es relevante. Si el contexto no "
                "alcanza, respondé con tu conocimiento general, indicando que no "
                "estaba guardado en la memoria local."
            )

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            logger.warning(f"No se pudo contactar a Ollama en {self.host}: {exc}")
            raise OllamaUnavailableError(str(exc)) from exc

        if resp.status_code != 200:
            raise OllamaUnavailableError(f"Ollama devolvió status {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        return data.get("response", "").strip()
