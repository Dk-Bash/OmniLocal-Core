import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_patterns.models import MaintenancePattern
from maintenance_patterns.manager import MaintenancePatternManager
from maintenance_knowledge.manager import MaintenanceKnowledgeManager


def test_pattern_model_validation():
    pat = MaintenancePattern(
        pattern_type="frequent_success",
        occurrences=3,
        confidence=0.85,
        description="Patrón de prueba",
    )
    assert pat.pattern_type == "frequent_success"
    assert pat.occurrences == 3

    with pytest.raises(ValueError):
        MaintenancePattern(
            pattern_type="invalid_pattern",
            confidence=0.5,
        )

    with pytest.raises(ValueError):
        MaintenancePattern(
            pattern_type="frequent_success",
            confidence=-0.1,
        )


def test_detect_patterns_from_knowledge():
    db = SQLiteManager(":memory:")
    k_mgr = MaintenanceKnowledgeManager(db_manager=db)
    p_mgr = MaintenancePatternManager(db_manager=db, knowledge_manager=k_mgr)

    fb1 = db.insert_execution_feedback(result_id=1, feedback_type="positive", quality_score=0.9, learning_notes="OK")
    fb2 = db.insert_execution_feedback(result_id=2, feedback_type="positive", quality_score=0.95, learning_notes="OK")
    fb3 = db.insert_execution_feedback(result_id=3, feedback_type="negative", quality_score=0.2, learning_notes="Fail")

    k_mgr.extract_knowledge(feedback_id=fb1)
    k_mgr.extract_knowledge(feedback_id=fb2)
    k_mgr.extract_knowledge(feedback_id=fb3)

    knowledge_before = list(k_mgr.get_all_knowledge())

    detected = p_mgr.detect_patterns()
    assert len(detected) == 2

    types = [p.pattern_type for p in detected]
    assert "frequent_success" in types
    assert "frequent_failure" in types

    knowledge_after = list(k_mgr.get_all_knowledge())
    assert knowledge_before == knowledge_after


def test_pattern_occurrences_count():
    db = SQLiteManager(":memory:")
    k_mgr = MaintenanceKnowledgeManager(db_manager=db)
    p_mgr = MaintenancePatternManager(db_manager=db, knowledge_manager=k_mgr)

    for i in range(4):
        fb = db.insert_execution_feedback(result_id=i+1, feedback_type="positive", quality_score=0.9, learning_notes="OK")
        k_mgr.extract_knowledge(feedback_id=fb)

    detected = p_mgr.detect_patterns()
    success_pat = [p for p in detected if p.pattern_type == "frequent_success"][0]
    assert success_pat.occurrences == 4
