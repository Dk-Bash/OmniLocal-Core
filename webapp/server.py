"""
Backend web de OmniLocal-Core.

Expone el asistente local (memoria, conocimiento, Ollama) como una API HTTP
que consume la interfaz gráfica. Corre exclusivamente en 127.0.0.1: no
escucha en la red, no hay ningún tráfico que salga de la máquina salvo el
que el propio Ollama haga (que también es local).
"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ingestion import SourceIngestor

app = FastAPI(title="OmniLocal-Core API")

# La UI puede correr en otro puerto durante desarrollo (Vite); en el
# instalado final, backend y frontend se sirven del mismo origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = OmniLocalEngine()
engine.start()
assistant = LocalAssistant(engine=engine)
ingestor = SourceIngestor(engine=engine)


# ----------------------------------------------------------------
# Esquemas de request/response
# ----------------------------------------------------------------
class NewSessionRequest(BaseModel):
    title: Optional[str] = None


class RenameSessionRequest(BaseModel):
    title: str


class AskRequest(BaseModel):
    content: str


class FactRequest(BaseModel):
    content: str
    importance: float = 0.7


class FeedbackRequest(BaseModel):
    conversation_id: int
    useful: bool


class SourceRequest(BaseModel):
    path: str


class GoalRequest(BaseModel):
    content: str


# ----------------------------------------------------------------
# Chequeo rápido de arranque (usado por el lanzador de escritorio)
# ----------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True}


# ----------------------------------------------------------------
# Estado del motor
# ----------------------------------------------------------------
@app.get("/api/status")
def get_status():
    status = engine.status()
    ollama = assistant.ollama
    ollama_running = ollama.is_available()
    memories_count = len(engine.get_all_memories())
    feedback_stats = engine.db_manager.get_feedback_stats()
    return {
        "engine": status,
        "ollama": {
            "available": ollama_running,
            "host": ollama.host,
            "model": ollama.model,
            "model_downloaded": ollama.has_model() if ollama_running else False,
        },
        "memory_count": memories_count,
        "feedback": feedback_stats,
    }


# ----------------------------------------------------------------
# Sesiones de charla (sidebar de historial)
# ----------------------------------------------------------------
@app.get("/api/sessions")
def list_sessions():
    return engine.db_manager.get_chat_sessions()


@app.post("/api/sessions")
def create_session(req: NewSessionRequest):
    title = req.title or "Nueva charla"
    session_id = engine.db_manager.insert_chat_session(title)
    return engine.db_manager.get_chat_session(session_id)


@app.patch("/api/sessions/{session_id}")
def rename_session(session_id: int, req: RenameSessionRequest):
    if not engine.db_manager.get_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    engine.db_manager.rename_chat_session(session_id, req.title)
    return engine.db_manager.get_chat_session(session_id)


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int):
    engine.db_manager.delete_chat_session(session_id)
    return {"deleted": True}


@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: int):
    if not engine.db_manager.get_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    conversations = engine.db_manager.get_conversations(session_id=session_id)
    return [_conversation_to_messages(c) for c in conversations]


@app.post("/api/sessions/{session_id}/messages")
def post_session_message(session_id: int, req: AskRequest):
    if not engine.db_manager.get_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    result = assistant.ask(req.content, session_id=session_id)
    return {
        "answer": result.answer,
        "source": result.source,
        "used_model": result.used_model,
        "conversation_id": result.conversation_id,
    }


def _conversation_to_messages(conv: dict) -> dict:
    return {
        "id": conv["id"],
        "user_input": conv["user_input"],
        "assistant_response": conv["assistant_response"],
        "created_at": conv["created_at"],
    }


# ----------------------------------------------------------------
# Hechos guardados explícitamente (panel "Contexto & Memoria")
# ----------------------------------------------------------------
@app.get("/api/facts")
def list_facts():
    memories = engine.get_all_memories()
    facts = [m for m in memories if m.memory_type == "hecho"]
    return [
        {
            "id": f.id,
            "category": "Hecho guardado",
            "detail": f.content,
            "confidence": f.importance,
        }
        for f in facts
    ]


@app.post("/api/facts")
def add_fact(req: FactRequest):
    mem_id = assistant.remember(req.content, importance=req.importance)
    return {"id": mem_id, "category": "Hecho guardado", "detail": req.content, "confidence": req.importance}


# ----------------------------------------------------------------
# Feedback (útil / no útil)
# ----------------------------------------------------------------
@app.post("/api/feedback")
def add_feedback(req: FeedbackRequest):
    assistant.feedback(req.conversation_id, req.useful)
    return {"ok": True}


# ----------------------------------------------------------------
# Fuentes locales (ingestión de carpetas/archivos)
# ----------------------------------------------------------------
@app.get("/api/sources")
def list_sources():
    return engine.db_manager.get_sources()


@app.post("/api/sources")
def add_source(req: SourceRequest):
    result = ingestor.ingest_path(req.path)
    return {
        "path": result.path,
        "files_found": result.files_found,
        "files_indexed": result.files_indexed,
        "errors": result.errors,
    }


@app.delete("/api/sources/{source_id}")
def delete_source(source_id: int):
    engine.db_manager.delete_source(source_id)
    return {"deleted": True}


# ----------------------------------------------------------------
# Objetivos / recordatorios (Bloque 9 -- Goal & Reminder Foundation)
# ----------------------------------------------------------------
@app.get("/api/goals")
def list_goals(status: Optional[str] = None):
    if status == "pendiente":
        goals = assistant.goal_manager.list_pending()
    else:
        goals = assistant.goal_manager.list_all()
    return [g.model_dump() for g in goals]


@app.post("/api/goals")
def create_goal(req: GoalRequest):
    goal_id = assistant.goal_manager.create_goal(req.content)
    return assistant.goal_manager.get_goal(goal_id).model_dump()


@app.post("/api/goals/{goal_id}/complete")
def complete_goal(goal_id: int):
    ok = assistant.goal_manager.complete_goal(goal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    return assistant.goal_manager.get_goal(goal_id).model_dump()


@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int):
    ok = assistant.goal_manager.delete_goal(goal_id)
    return {"deleted": ok}


# ----------------------------------------------------------------
# Archivos estáticos de la interfaz (build de Vite), si existen
# ----------------------------------------------------------------
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
