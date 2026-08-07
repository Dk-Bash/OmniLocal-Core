"""
Interfaz de consola de OmniLocal-Core.

Este es el punto de entrada pensado para uso real: un chat en la terminal
que guarda memoria, consulta al modelo de IA local cuando hace falta, y
aprende de cada conversación para depender cada vez menos del modelo.

Uso:
    python app/cli.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ollama_client import OllamaClient
from local_ai.knowledge_observability import build_review_candidates
from local_ai.review_actions import confirm_memory, correct_memory, ignore_memory
from local_ai.project_scanner import scan_project_structure, generate_status_summary, read_readme
from local_ai.code_analyzer import scan_project_code
from project.manager import ProjectManager

BANNER = r"""
╔══════════════════════════════════════════════╗
║              OmniLocal-Core                   ║
║   Asistente local · sin internet · sin nube    ║
╚══════════════════════════════════════════════╝
Escribí una pregunta y Enter. Comandos disponibles:
  /recordar <texto>   -> guarda algo en la memoria local
  /memorias           -> muestra las últimas memorias guardadas
  /pendientes         -> muestra los objetivos/recordatorios pendientes
  /completar <id>     -> marca un objetivo como completado
  /revisar            -> muestra memorias candidatas a revisión
  /revisar N confirmar          -> confirma el candidato N de la última lista
  /revisar N corregir <texto>   -> corrige el candidato N con texto nuevo
  /revisar N ignorar            -> ignora el candidato N (no se muestra más)
  /proyecto agregar <ruta>      -> escanea una carpeta y la registra como proyecto
  /proyectos                    -> lista los proyectos registrados
  /proyecto archivos <id>       -> lista clases/funciones/imports encontrados
  /proyecto resumir <id>        -> genera un resumen narrativo con el modelo (bajo demanda)
  /proyecto usar <id>           -> activa un proyecto para esta charla (por id, sin ambigüedad)
  /proyecto activo              -> muestra cuál proyecto está activo en esta charla
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


def print_pending_goals(assistant: LocalAssistant) -> None:
    pending = assistant.goal_manager.list_pending()
    if not pending:
        print("No hay objetivos/recordatorios pendientes.")
        return
    for goal in pending:
        print(f"  [{goal.id}] {goal.content}")


def print_review_candidates(candidates: list) -> None:
    if not candidates:
        print("No hay memorias candidatas a revisión ahora mismo.")
        return
    for i, candidate in enumerate(candidates, start=1):
        reasons = ", ".join(candidate["reasons"])
        print(f"  {i}. {candidate['content']}  ({reasons})")


def main() -> None:
    print(BANNER)
    engine = OmniLocalEngine()
    engine.start()
    assistant = LocalAssistant(engine=engine)
    project_manager = ProjectManager(db_manager=engine.db_manager)

    # Bloque 16: antes, cada mensaje de la CLI corría con session_id=None,
    # así que el contexto conversacional del Bloque 2 nunca se activaba
    # acá (solo en la interfaz web). Ahora se crea una sesión real al
    # arrancar y se reusa para toda la charla -- esto también deja
    # funcionando, de paso, la memoria corta de conversación en consola.
    session_id = engine.db_manager.insert_chat_session("Consola")

    print_status(engine, assistant.ollama)
    print()

    last_review_candidates: list = []

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
        elif user_input == "/pendientes":
            print_pending_goals(assistant)
            continue
        elif user_input.startswith("/completar "):
            raw_id = user_input[len("/completar "):].strip()
            if raw_id.isdigit() and assistant.goal_manager.complete_goal(int(raw_id)):
                print(f"Objetivo {raw_id} marcado como completado.")
            else:
                print("Uso: /completar <id> (ver /pendientes para los ids)")
            continue
        elif user_input == "/revisar":
            last_review_candidates = build_review_candidates(engine)
            print_review_candidates(last_review_candidates)
            continue
        elif user_input.startswith("/revisar "):
            parts = user_input[len("/revisar "):].strip().split(maxsplit=2)
            if not parts or not parts[0].isdigit():
                print("Uso: /revisar N confirmar | /revisar N corregir <texto> | /revisar N ignorar")
                continue
            index = int(parts[0])
            action = parts[1].lower() if len(parts) > 1 else ""
            if not last_review_candidates or not (1 <= index <= len(last_review_candidates)):
                print("Ese número no corresponde a la última lista de /revisar. Corré /revisar de nuevo.")
                continue
            memory_id = last_review_candidates[index - 1]["id"]

            if action == "confirmar":
                confirm_memory(engine, memory_id)
                print(f"Confirmado. Gracias, ajusté la confianza de esa memoria.")
            elif action == "corregir":
                new_content = parts[2].strip() if len(parts) > 2 else ""
                if not new_content:
                    print("Uso: /revisar N corregir <texto nuevo>")
                    continue
                correct_memory(engine, memory_id, new_content)
                print(f"Corregido: ahora dice '{new_content}'.")
            elif action == "ignorar":
                ignore_memory(engine, memory_id)
                print("Listo, no te lo vuelvo a mostrar.")
            else:
                print("Uso: /revisar N confirmar | /revisar N corregir <texto> | /revisar N ignorar")
            continue
        elif user_input.startswith("/proyecto agregar "):
            raw_path = user_input[len("/proyecto agregar "):].strip()
            if not raw_path:
                print("Uso: /proyecto agregar <ruta de la carpeta>")
                continue
            result = scan_project_structure(raw_path)
            if not result.structure_summary:
                print(f"No pude leer esa carpeta: {raw_path}")
                continue
            existing = project_manager.get_project_by_path(result.path)
            if existing is not None:
                project_manager.update_project(existing.id, structure_summary=result.structure_summary, technologies=result.technologies, reindex=True)
                project_id = existing.id
                print(f"Proyecto '{existing.name}' actualizado (ID {existing.id}).")
            else:
                name = os.path.basename(result.path.rstrip(os.sep)) or result.path
                project_id = project_manager.create_project(name, result.path, technologies=result.technologies, structure_summary=result.structure_summary)
                print(f"Proyecto '{name}' registrado (ID {project_id}). Tecnologías detectadas: {result.technologies or 'ninguna reconocida'}.")

            # Bloque 15: reindexado = reemplazo completo de project_files.
            engine.db_manager.delete_project_files(project_id)
            file_analyses = scan_project_code(result.path)
            for fa in file_analyses:
                engine.db_manager.insert_project_file(
                    project_id, fa.relative_path, fa.language,
                    json.dumps(fa.classes), json.dumps(fa.functions), json.dumps(fa.imports),
                    parse_error=fa.parse_error,
                )
            analyzed_ok = sum(1 for fa in file_analyses if fa.parse_error is None)
            if file_analyses:
                print(f"Código analizado: {analyzed_ok}/{len(file_analyses)} archivos Python procesados.")
            continue
        elif user_input.startswith("/proyecto archivos "):
            raw_id = user_input[len("/proyecto archivos "):].strip()
            if not raw_id.isdigit():
                print("Uso: /proyecto archivos <id> (ver /proyectos para los ids)")
                continue
            files = engine.db_manager.get_project_files(int(raw_id))
            if not files:
                print("No hay archivos analizados para ese proyecto todavía (¿corriste /proyecto agregar?).")
                continue
            for f in files:
                if f["parse_error"]:
                    print(f"  {f['relative_path']}: (no se pudo analizar: {f['parse_error']})")
                    continue
                classes = json.loads(f["classes"])
                functions = json.loads(f["functions"])
                print(f"  {f['relative_path']}: clases={classes} funciones={functions}")
            continue
        elif user_input == "/proyectos":
            projects = project_manager.list_projects()
            if not projects:
                print("Todavía no hay proyectos registrados. Usá /proyecto agregar <ruta>.")
            for p in projects:
                print(f"  [{p.id}] {p.name} -- {p.technologies or 'tecnología no detectada'} ({p.path})")
            continue
        elif user_input.startswith("/proyecto resumir "):
            raw_id = user_input[len("/proyecto resumir "):].strip()
            if not raw_id.isdigit():
                print("Uso: /proyecto resumir <id> (ver /proyectos para los ids)")
                continue
            project = project_manager.get_project(int(raw_id))
            if project is None:
                print("No encontré ese proyecto.")
                continue
            readme = read_readme(project.path)
            summary = generate_status_summary(project.structure_summary or "", assistant.ollama, readme_content=readme)
            if summary is None:
                print("No pude generar el resumen (¿Ollama está corriendo?).")
                continue
            project_manager.update_project(project.id, status_summary=summary)
            print(f"Resumen: {summary}")
            continue
        elif user_input.startswith("/proyecto usar "):
            raw_id = user_input[len("/proyecto usar "):].strip()
            if not raw_id.isdigit():
                print("Uso: /proyecto usar <id> (ver /proyectos para los ids)")
                continue
            project = project_manager.get_project(int(raw_id))
            if project is None:
                print("No encontré ese proyecto.")
                continue
            engine.db_manager.set_session_project(session_id, project.id)
            print(f"Listo, activé el proyecto '{project.name}'.")
            continue
        elif user_input == "/proyecto activo":
            session = engine.db_manager.get_chat_session(session_id)
            active_id = session.get("active_project_id") if session else None
            if not active_id:
                print("No hay ningún proyecto activo en esta charla.")
            else:
                project = project_manager.get_project(active_id)
                print(f"Proyecto activo: {project.name if project else '(desconocido)'} (ID {active_id}).")
            continue
        elif user_input.startswith("/recordar "):
            content = user_input[len("/recordar "):].strip()
            if content:
                mem_id = assistant.remember(content)
                print(f"Guardado en memoria (ID {mem_id}).")
            else:
                print("Uso: /recordar <texto a guardar>")
            continue

        result = assistant.ask(user_input, session_id=session_id)
        prefix = {
            "memoria_local": "[memoria]",
            "modelo_ia": "[IA local]",
            "sin_modelo": "[sin modelo]",
            "vacio": "[-]",
        }.get(result.source, "")
        print(f"omni {prefix}> {result.answer}\n")


if __name__ == "__main__":
    main()
