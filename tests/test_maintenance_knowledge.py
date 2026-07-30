import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_knowledge.models import KnowledgeEntry
from maintenance_knowledge.manager import MaintenanceKnowledgeManager


def test_knowledge_entry_validation():
    entry = KnowledgeEntry(
        source_feedback_id=1,
        knowledge_type="success_pattern",
        description="Test description",
        confidence=0.9,
    )
    assert entry.confidence == 0.9
    assert entry.knowledge_type == "success_pattern"

    with pytest.raises(ValueError):
        KnowledgeEntry(
            source_feedback_id=1,
            knowledge_type="invalid_type",
            confidence=0.5,
        )

    with pytest.raises(ValueError):
        KnowledgeEntry(
            source_feedback_id=1,
            knowledge_type="success_pattern",
            confidence=1.5,
        )


def test_extract_knowledge_positive():
    db = SQLiteManager(":memory:")
    mgr = MaintenanceKnowledgeManager(db_manager=db)

    fb_id = db.insert_execution_feedback(result_id=1, feedback_type="positive", quality_score=0.95, learning_notes="Excelente")
    entry = mgr.extract_knowledge(feedback_id=fb_id)

    assert entry.knowledge_type == "success_pattern"
    assert entry.confidence == 0.9
    assert entry.source_feedback_id == fb_id

    stored = db.get_knowledge(entry.id)
    assert stored is not None
    assert stored["knowledge_type"] == "success_pattern"


def test_extract_knowledge_negative():
    db = SQLiteManager(":memory:")
    mgr = MaintenanceKnowledgeManager(db_manager=db)

    fb_id = db.insert_execution_feedback(result_id=1, feedback_type="negative", quality_score=0.2, learning_notes="Error de ejecución")
    entry = mgr.extract_knowledge(feedback_id=fb_id)

    assert entry.knowledge_type == "failure_pattern"
    assert entry.confidence == 0.8
    assert entry.source_feedback_id == fb_id


def test_extract_knowledge_neutral():
    db = SQLiteManager(":memory:")
    mgr = MaintenanceKnowledgeManager(db_manager=db)

    fb_id = db.insert_execution_feedback(result_id=1, feedback_type="neutral", quality_score=0.5, learning_notes="Parcialmente correcto")
    entry = mgr.extract_knowledge(feedback_id=fb_id)

    assert entry.knowledge_type == "improvement_hint"
    assert entry.confidence == 0.5
    assert entry.source_feedback_id == fb_id


def test_get_all_knowledge():
    db = SQLiteManager(":memory:")
    mgr = MaintenanceKnowledgeManager(db_manager=db)

    fb1 = db.insert_execution_feedback(result_id=1, feedback_type="positive", quality_score=0.9, learning_notes="N/A")
    fb2 = db.insert_execution_feedback(result_id=2, feedback_type="negative", quality_score=0.3, learning_notes="N/A")

    mgr.extract_knowledge(feedback_id=fb1)
    mgr.extract_knowledge(feedback_id=fb2)

    all_k = mgr.get_all_knowledge()
    assert len(all_k) == 2
