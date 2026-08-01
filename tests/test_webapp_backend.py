import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from database.sqlite_manager import SQLiteManager
from app.core.engine import OmniLocalEngine
from local_ai.assistant import LocalAssistant
from local_ai.ingestion import SourceIngestor
import webapp.server as server_module


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    eng = OmniLocalEngine(db_manager=db_manager)
    eng.start()

    # Reemplaza las instancias globales del server por unas aisladas para el test.
    server_module.engine = eng
    server_module.assistant = LocalAssistant(engine=eng)
    server_module.ingestor = SourceIngestor(engine=eng)

    with TestClient(server_module.app) as c:
        yield c

    db_manager.close()
    os.remove(path)


def test_status_endpoint(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["engine"]["status"] == "ready"
    assert "ollama" in data


def test_health_endpoint_is_lightweight(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_session_lifecycle(client):
    r = client.post("/api/sessions", json={"title": "Mi charla"})
    assert r.status_code == 200
    session = r.json()
    assert session["title"] == "Mi charla"

    r = client.get("/api/sessions")
    assert len(r.json()) == 1

    r = client.patch(f"/api/sessions/{session['id']}", json={"title": "Renombrada"})
    assert r.json()["title"] == "Renombrada"

    r = client.delete(f"/api/sessions/{session['id']}")
    assert r.json()["deleted"] is True
    assert client.get("/api/sessions").json() == []


def test_message_flow_memory_and_facts(client):
    session = client.post("/api/sessions", json={"title": "Charla"}).json()

    client.post("/api/facts", json={"content": "El wifi es RedCasa123", "importance": 0.8})

    r = client.post(f"/api/sessions/{session['id']}/messages", json={"content": "RedCasa123"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "memoria_local"
    assert body["used_model"] is False
    assert "RedCasa123" in body["answer"]

    r = client.get("/api/facts")
    facts = r.json()
    assert any("RedCasa123" in f["detail"] for f in facts)

    r = client.get(f"/api/sessions/{session['id']}/messages")
    messages = r.json()
    assert len(messages) == 1
    assert messages[0]["user_input"] == "RedCasa123"


def test_feedback_updates_status(client):
    session = client.post("/api/sessions", json={"title": "Charla"}).json()
    client.post("/api/facts", json={"content": "Dato de prueba XYZ"})
    r = client.post(f"/api/sessions/{session['id']}/messages", json={"content": "XYZ"})
    conv_id = r.json()["conversation_id"]

    r = client.post("/api/feedback", json={"conversation_id": conv_id, "useful": True})
    assert r.status_code == 200

    status = client.get("/api/status").json()
    assert status["feedback"]["useful"] == 1


def test_source_ingestion(client, tmp_path):
    notes_dir = tmp_path / "notas"
    notes_dir.mkdir()
    (notes_dir / "info.md").write_text("El horario del taller es de 9 a 18 horas.")

    r = client.post("/api/sources", json={"path": str(notes_dir)})
    assert r.status_code == 200
    result = r.json()
    assert result["files_indexed"] == 1

    r = client.get("/api/sources")
    sources = r.json()
    assert len(sources) == 1
    assert sources[0]["file_count"] == 1

    session = client.post("/api/sessions", json={"title": "Charla"}).json()
    r = client.post(f"/api/sessions/{session['id']}/messages", json={"content": "horario del taller"})
    assert "9 a 18" in r.json()["answer"]
