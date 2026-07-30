import pytest
import os
import tempfile
from database.sqlite_manager import SQLiteManager
from maintenance_correlation.models import IntelligenceCorrelation
from maintenance_correlation.manager import MaintenanceCorrelationManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_omnilocal.db")
    db_mgr = SQLiteManager(db_path=db_path)
    db_mgr.create_tables()
    yield db_mgr
    db_mgr.close()


def test_correlation_model_validations():
    # Valid correlation
    corr = IntelligenceCorrelation(
        strategy_type="adaptive",
        pattern_type="successful_strategy",
        success_rate=0.85,
        sample_size=10,
        confidence=0.9,
        description="Correlación válida.",
    )
    assert corr.success_rate == 0.85

    # Invalid success_rate
    with pytest.raises(ValueError):
        IntelligenceCorrelation(
            strategy_type="adaptive",
            pattern_type="test",
            success_rate=1.5,
            sample_size=5,
            confidence=0.8,
            description="Inválido",
        )

    # Invalid confidence
    with pytest.raises(ValueError):
        IntelligenceCorrelation(
            strategy_type="adaptive",
            pattern_type="test",
            success_rate=0.8,
            sample_size=5,
            confidence=-0.1,
            description="Inválido",
        )

    # Invalid sample_size
    with pytest.raises(ValueError):
        IntelligenceCorrelation(
            strategy_type="adaptive",
            pattern_type="test",
            success_rate=0.8,
            sample_size=-1,
            confidence=0.8,
            description="Inválido",
        )


def test_maintenance_correlation_manager_generation(temp_db):
    manager = MaintenanceCorrelationManager(db_manager=temp_db)
    correlations = manager.generate_correlations()

    assert len(correlations) > 0
    first_corr = correlations[0]
    assert first_corr.id is not None
    assert 0.0 <= first_corr.success_rate <= 1.0
    assert 0.0 <= first_corr.confidence <= 1.0

    stored = manager.get_correlation(first_corr.id)
    assert stored is not None
    assert stored["strategy_type"] == first_corr.strategy_type

    all_corrs = manager.get_correlations()
    assert len(all_corrs) >= len(correlations)
