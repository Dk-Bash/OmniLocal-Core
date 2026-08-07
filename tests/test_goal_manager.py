import os
import tempfile

import pytest

from database.sqlite_manager import SQLiteManager
from goals.manager import GoalManager


@pytest.fixture
def manager():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_manager = SQLiteManager(db_path=path)
    db_manager.connect()
    db_manager.create_tables()
    yield GoalManager(db_manager=db_manager)
    db_manager.close()
    os.remove(path)


def test_create_goal_returns_id_and_defaults_to_pendiente(manager):
    goal_id = manager.create_goal("Comprar pan")
    goal = manager.get_goal(goal_id)
    assert goal is not None
    assert goal.content == "Comprar pan"
    assert goal.status == "pendiente"
    assert goal.completed_at is None


def test_list_pending_only_includes_pending(manager):
    id1 = manager.create_goal("Tarea 1")
    id2 = manager.create_goal("Tarea 2")
    manager.complete_goal(id1)

    pending = manager.list_pending()
    assert len(pending) == 1
    assert pending[0].id == id2


def test_list_all_includes_completed_and_pending(manager):
    id1 = manager.create_goal("Tarea 1")
    manager.create_goal("Tarea 2")
    manager.complete_goal(id1)

    all_goals = manager.list_all()
    assert len(all_goals) == 2


def test_complete_goal_sets_status_and_completed_at(manager):
    goal_id = manager.create_goal("Tarea")
    ok = manager.complete_goal(goal_id)
    assert ok is True

    goal = manager.get_goal(goal_id)
    assert goal.status == "completado"
    assert goal.completed_at is not None


def test_complete_nonexistent_goal_returns_false(manager):
    assert manager.complete_goal(9999) is False


def test_delete_goal(manager):
    goal_id = manager.create_goal("Tarea")
    assert manager.delete_goal(goal_id) is True
    assert manager.get_goal(goal_id) is None


def test_get_nonexistent_goal_returns_none(manager):
    assert manager.get_goal(9999) is None
