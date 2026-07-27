from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StrategyLearningReport(BaseModel):
    """
    Modelo de datos para el reporte de aprendizaje de estrategias de mantenimiento (Módulo 28).
    Sintetiza métricas históricas de evaluaciones estratégicas para responder
    qué estrategias han mostrado mejores resultados anteriormente.
    """

    id: Optional[int] = None
    total_evaluations: int = Field(
        ..., description="Número total de evaluaciones estratégicas analizadas"
    )
    average_quality_score: float = Field(
        ..., description="Puntuación promedio de calidad estratégica"
    )
    average_impact_score: float = Field(
        ..., description="Puntuación promedio de impacto esperado"
    )
    average_confidence_score: float = Field(
        ..., description="Puntuación promedio de confianza técnica"
    )
    best_strategy_type: Optional[str] = Field(
        None, description="Tipo o categoría de estrategia con mejor desempeño histórico"
    )
    learning_summary: str = Field(
        ..., description="Resumen cualitativo del análisis de aprendizaje estratégico"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de generación del reporte"
    )
