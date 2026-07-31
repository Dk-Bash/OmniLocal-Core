from typing import Optional, List, Dict, Any
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.observability.manager import RuntimeObservabilityManager
from omnilocal_runtime.validation.manager import RuntimeValidationManager
from omnilocal_runtime.learning.models import RuntimeLearningRecord, RuntimeAdaptationRecommendation
from omnilocal_runtime.learning.patterns import RuntimePatternAnalyzer
from omnilocal_runtime.learning.adaptation import RuntimeAdaptationEngine


class RuntimeLearningManager:
    """
    Gestor Principal de Aprendizaje y Adaptación del Runtime (Runtime Block 08).
    Analiza ejecuciones históricas, detecta patrones, genera aprendizajes y recomendaciones sin alterar nada existente.
    """

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        obs_manager: Optional[RuntimeObservabilityManager] = None,
        val_manager: Optional[RuntimeValidationManager] = None
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.obs_manager = obs_manager or RuntimeObservabilityManager(db_manager=self.db_manager)
        self.val_manager = val_manager or RuntimeValidationManager(db_manager=self.db_manager)

    def generate_learning_record(
        self,
        learning_type: str,
        pattern_detected: str,
        source_execution_id: int = 0,
        source_decision_id: int = 0,
        confidence: float = 0.0,
        impact_prediction: str = ""
    ) -> RuntimeLearningRecord:
        """
        Persiste un registro de aprendizaje en SQLite y devuelve la instancia del modelo.
        """
        record_id = self.db_manager.insert_learning_record(
            learning_type=learning_type,
            pattern_detected=pattern_detected,
            source_execution_id=source_execution_id,
            source_decision_id=source_decision_id,
            confidence=confidence,
            impact_prediction=impact_prediction
        )

        return RuntimeLearningRecord(
            id=record_id,
            source_execution_id=source_execution_id,
            source_decision_id=source_decision_id,
            learning_type=learning_type,
            pattern_detected=pattern_detected,
            confidence=confidence,
            impact_prediction=impact_prediction
        )

    def generate_adaptation_recommendation(
        self,
        learning_id: int,
        target_area: str,
        recommended_change: str,
        priority: str = "medium",
        confidence: float = 0.0,
        reasoning: str = ""
    ) -> RuntimeAdaptationRecommendation:
        """
        Persiste una recomendación de adaptación en SQLite y devuelve la instancia del modelo.
        """
        adaptation_id = self.db_manager.insert_adaptation(
            learning_id=learning_id,
            target_area=target_area,
            recommended_change=recommended_change,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning
        )

        return RuntimeAdaptationRecommendation(
            id=adaptation_id,
            learning_id=learning_id,
            target_area=target_area,
            recommended_change=recommended_change,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning
        )

    def analyze_execution_history(self) -> Dict[str, Any]:
        """
        Analiza el historial de ejecuciones y validaciones, genera automáticamente
        registros de aprendizaje y recomendaciones de adaptación en la base de datos.
        """
        validation_reports = self.val_manager.get_reports()
        performance_reports = self.obs_manager.get_reports()

        total_execs = len(validation_reports) + len(performance_reports)

        failure_patterns = RuntimePatternAnalyzer.detect_failure_patterns(validation_reports)
        success_patterns = RuntimePatternAnalyzer.detect_success_patterns(validation_reports)

        generated_learnings: List[RuntimeLearningRecord] = []
        generated_adaptations: List[RuntimeAdaptationRecommendation] = []

        if failure_patterns:
            for fp in failure_patterns:
                target = fp["target_area"]
                occurrences = fp["occurrences"]
                confidence = RuntimeAdaptationEngine.calculate_learning_confidence(occurrences, max(total_execs, 1))

                learning = self.generate_learning_record(
                    learning_type="failure_pattern",
                    pattern_detected=f"{target}_instability",
                    confidence=confidence,
                    impact_prediction=f"Reducción estimada de fallos en '{target}' al implementar salvaguardas."
                )
                generated_learnings.append(learning)

                adaptation = RuntimeAdaptationEngine.generate_adaptation(learning)
                saved_adaptation = self.generate_adaptation_recommendation(
                    learning_id=learning.id or 0,
                    target_area=adaptation.target_area,
                    recommended_change=adaptation.recommended_change,
                    priority=adaptation.priority,
                    confidence=adaptation.confidence,
                    reasoning=adaptation.reasoning
                )
                generated_adaptations.append(saved_adaptation)

        else:
            confidence = RuntimeAdaptationEngine.calculate_learning_confidence(1, max(total_execs, 1))
            learning = self.generate_learning_record(
                learning_type="optimization",
                pattern_detected="high_runtime_stability",
                confidence=confidence,
                impact_prediction="Mejora en latencia y consumo de recursos."
            )
            generated_learnings.append(learning)

            adaptation = RuntimeAdaptationEngine.generate_adaptation(learning)
            saved_adaptation = self.generate_adaptation_recommendation(
                learning_id=learning.id or 0,
                target_area=adaptation.target_area,
                recommended_change=adaptation.recommended_change,
                priority=adaptation.priority,
                confidence=adaptation.confidence,
                reasoning=adaptation.reasoning
            )
            generated_adaptations.append(saved_adaptation)

        return {
            "total_executions_analyzed": total_execs,
            "failure_patterns_detected": len(failure_patterns),
            "success_patterns_detected": len(success_patterns),
            "learnings_generated": [l.to_dict() for l in generated_learnings],
            "adaptations_generated": [a.to_dict() for a in generated_adaptations]
        }

    def get_learning_records(self) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de aprendizaje almacenados en SQLite."""
        return self.db_manager.get_learning_records()

    def get_adaptations(self) -> List[Dict[str, Any]]:
        """Obtiene todas las recomendaciones de adaptación almacenadas en SQLite."""
        return self.db_manager.get_adaptations()
