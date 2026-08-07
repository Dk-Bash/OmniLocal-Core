import os
import tempfile
import time

import pytest

from database.sqlite_manager import SQLiteManager
from project.manager import ProjectManager


@pytest.fixture
def manager():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    yield ProjectManager(db_manager=db_manager)
    db_manager.close()
    os.remove(path)


def test_create_project(manager):
    project_id = manager.create_project("App Diccionario", "/home/user/dict-app", technologies="Python, SQLite")
    project = manager.get_project(project_id)
    assert project is not None
    assert project.name == "App Diccionario"
    assert project.path == "/home/user/dict-app"
    assert project.technologies == "Python, SQLite"
    assert project.objective is None
    assert project.status_summary is None
    assert project.last_indexed_at is not None  # se setea al crear


def test_get_project_by_path(manager):
    manager.create_project("App Diccionario", "/home/user/dict-app")
    project = manager.get_project_by_path("/home/user/dict-app")
    assert project is not None
    assert project.name == "App Diccionario"


def test_get_project_by_path_not_found(manager):
    assert manager.get_project_by_path("/no/existe") is None


def test_list_projects(manager):
    manager.create_project("Proyecto A", "/a")
    manager.create_project("Proyecto B", "/b")
    projects = manager.list_projects()
    assert len(projects) == 2


def test_update_project_objective_and_status_summary(manager):
    project_id = manager.create_project("App Diccionario", "/home/user/dict-app")
    ok = manager.update_project(project_id, objective="Herramienta para estudiar idiomas", status_summary="Flashcards listas, verbos pendientes")
    assert ok is True

    project = manager.get_project(project_id)
    assert project.objective == "Herramienta para estudiar idiomas"
    assert project.status_summary == "Flashcards listas, verbos pendientes"
    assert project.updated_at is not None


def test_update_project_reindex_bumps_last_indexed_at(manager):
    project_id = manager.create_project("App", "/app")
    first = manager.get_project(project_id).last_indexed_at
    time.sleep(1.1)
    manager.update_project(project_id, structure_summary="nueva estructura", reindex=True)
    second = manager.get_project(project_id).last_indexed_at
    assert second > first


def test_delete_project(manager):
    project_id = manager.create_project("App", "/app")
    assert manager.delete_project(project_id) is True
    assert manager.get_project(project_id) is None


def test_path_must_be_unique(manager):
    manager.create_project("App", "/app")
    with pytest.raises(Exception):
        manager.create_project("App otra vez", "/app")
