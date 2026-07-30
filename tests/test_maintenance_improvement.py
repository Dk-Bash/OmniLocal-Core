import pytest
from database.sqlite_manager import SQLiteManager
from maintenance_improvement.models import ImprovementRecommendation
from maintenance_improvement.manager import MaintenanceImprovementManager
from maintenance_patterns.manager import MaintenancePatternManager


def test_improvement_model_validation():
    rec = ImprovementRecommendation(
        pattern_id=1,
        recommendation_type="correction",
        priority="high",
        description="Ajuste requerido",
        confidence=0.9,
    )
    assert rec.recommendation_type == "correction"
    assert rec.priority == "high"

    with pytest.raises(ValueError):
        ImprovementRecommendation(
            pattern_id=1,
            recommendation_type="invalid_type",
            priority="high",
            confidence=0.8,
        )

    with pytest.raises(ValueError):
        ImprovementRecommendation(
            pattern_id=1,
            recommendation_type="correction",
            priority="critical",
            confidence=0.8,
        )


def test_generate_recommendations_rules():
    db = SQLiteManager(":memory:")
    p_mgr = MaintenancePatternManager(db_manager=db)
    i_mgr = MaintenanceImprovementManager(db_manager=db, pattern_manager=p_mgr)

    p_fail = p_mgr.detect_pattern(pattern_type="frequent_failure", occurrences=3, confidence=0.85)
    p_rec = p_mgr.detect_pattern(pattern_type="recurring_issue", occurrences=2, confidence=0.6)
    p_succ = p_mgr.detect_pattern(pattern_type="frequent_success", occurrences=5, confidence=0.95)

    patterns_before = list(p_mgr.get_patterns())

    recs = i_mgr.generate_recommendations()
    assert len(recs) == 3

    rec_by_pat = {r.pattern_id: r for r in recs}

    assert rec_by_pat[p_fail.id].recommendation_type == "correction"
    assert rec_by_pat[p_fail.id].priority == "high"

    assert rec_by_pat[p_rec.id].recommendation_type == "prevention"
    assert rec_by_pat[p_rec.id].priority == "medium"

    assert rec_by_pat[p_succ.id].recommendation_type == "optimization"
    assert rec_by_pat[p_succ.id].priority == "low"

    patterns_after = list(p_mgr.get_patterns())
    assert patterns_before == patterns_after


def test_read_only_integrity_guarantee():
    """Confirma que Bloque 9 no modifica datos previos (feedback, tracking, memorias)."""
    db = SQLiteManager(":memory:")
    db.create_tables()
    
    fb_id = db.insert_execution_feedback(result_id=1, feedback_type="negative", quality_score=0.1, learning_notes="Error crítico")
    fb_before = db.get_execution_feedback(fb_id)

    from maintenance_knowledge.manager import MaintenanceKnowledgeManager
    k_mgr = MaintenanceKnowledgeManager(db_manager=db)
    p_mgr = MaintenancePatternManager(db_manager=db, knowledge_manager=k_mgr)
    i_mgr = MaintenanceImprovementManager(db_manager=db, pattern_manager=p_mgr)

    k_entry = k_mgr.extract_knowledge(feedback_id=fb_id)
    p_objs = p_mgr.detect_patterns()
    recs = i_mgr.generate_recommendations()

    assert k_entry is not None
    assert len(p_objs) > 0
    assert len(recs) > 0

    fb_after = db.get_execution_feedback(fb_id)
    assert fb_before == fb_after
