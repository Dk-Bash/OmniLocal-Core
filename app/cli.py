"""
Interfaz de consola de OmniLocal-Core.

Este es el punto de entrada pensado para uso real: un chat en la terminal
que guarda memoria, consulta al modelo de IA local cuando hace falta, y
aprende de cada conversación para depender cada vez menos del modelo.

Uso:
    python app/cli.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient

BANNER = r"""
╔══════════════════════════════════════════════╗
║              OmniLocal-Core                   ║
║   Asistente local · sin internet · sin nube    ║
╚══════════════════════════════════════════════╝
Escribí una pregunta y Enter. Comandos disponibles:
  /recordar <texto>   -> guarda algo en la memoria local
  /memorias           -> muestra las últimas memorias guardadas
  /estado             -> estado del motor y del modelo de IA local
  /ayuda              -> muestra esta ayuda
  /salir              -> cierra el programa
"""


def print_status(engine: OmniLocalEngine, ollama: OllamaClient) -> None:
    status = engine.status()
    print(f"Motor: {status['name']} v{status['version']} — {status['status']}")
    ollama.ensure_running()
    if ollama.is_available():
        model_ok = ollama.has_model()
        print(f"IA local (Ollama): disponible en {ollama.host}")
        print(f"Modelo '{ollama.model}': {'descargado' if model_ok else 'NO descargado (ollama pull ' + ollama.model + ')'}")
    else:
        print(f"IA local (Ollama): no disponible en {ollama.host}")
        print("  -> El asistente sigue funcionando solo con memoria/conocimiento guardado.")


def print_recent_memories(engine: OmniLocalEngine, limit: int = 10) -> None:
    memories = engine.get_all_memories()
    if not memories:
        print("Todavía no hay memorias guardadas.")
        return
    for mem in memories[-limit:]:
        print(f"  [{mem.id}] ({mem.memory_type}, importancia {mem.importance}) {mem.content}")


def main() -> None:
    print(BANNER)
    engine = OmniLocalEngine()
    engine.start()
    assistant = LocalAssistant(engine=engine)

    print_status(engine, assistant.ollama)
    print()

    while True:
        try:
            user_input = input("vos> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not user_input:
            continue

        if user_input in ("/salir", "/exit", "/quit"):
            print("Hasta luego.")
            break
        elif user_input == "/ayuda":
            print(BANNER)
            continue
        elif user_input == "/estado":
            print_status(engine, assistant.ollama)
            continue
        elif user_input == "/memorias":
            print_recent_memories(engine)
            continue
        elif user_input.startswith("/recordar "):
            content = user_input[len("/recordar "):].strip()
            if content:
                mem_id = assistant.remember(content)
                print(f"Guardado en memoria (ID {mem_id}).")
            else:
                print("Uso: /recordar <texto a guardar>")
            continue

        result = assistant.ask(user_input)
        prefix = {
            "memoria_local": "[memoria]",
            "modelo_ia": "[IA local]",
            "sin_modelo": "[sin modelo]",
            "vacio": "[-]",
        }.get(result.source, "")
        print(f"omni {prefix}> {result.answer}\n")


if __name__ == "__main__":
    main()
