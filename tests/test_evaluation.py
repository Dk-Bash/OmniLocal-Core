import os
import unittest
import tempfile
from pydantic import ValidationError
from database.sqlite_manager import SQLiteManager
from evaluation.models import InteractionFeedback
from evaluation.manager import EvaluationManager


class TestEvaluation(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.eval_manager = EvaluationManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_and_get_feedback(self):
        """Prueba creación y recuperación de una evaluación por ID."""
        feedback_id = self.eval_manager.add_feedback(
            interaction_id=10,
            rating=5,
            confidence=0.9,
            comment="Muy útil"
        )
        self.assertIsNotNone(feedback_id)
        self.assertGreater(feedback_id, 0)

        feedback = self.eval_manager.get_feedback(feedback_id)
        self.assertIsNotNone(feedback)
        self.assertIsInstance(feedback, InteractionFeedback)
        self.assertEqual(feedback.interaction_id, 10)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.confidence, 0.9)
        self.assertEqual(feedback.comment, "Muy útil")

    def test_multiple_feedbacks_for_interaction(self):
        """Prueba asociar múltiples evaluaciones a una misma interacción y listar."""
        f1_id = self.eval_manager.add_feedback(
            interaction_id=1,
            rating=5,
            confidence=0.9,
            comment="Excelente"
        )
        f2_id = self.eval_manager.add_feedback(
            interaction_id=1,
            rating=4,
            confidence=0.85,
            comment="Muy buena respuesta"
        )

        feedbacks = self.eval_manager.get_interaction_feedback(interaction_id=1)
        self.assertEqual(len(feedbacks), 2)
        self.assertEqual(feedbacks[0].id, f1_id)
        self.assertEqual(feedbacks[0].rating, 5)
        self.assertEqual(feedbacks[0].comment, "Excelente")

        self.assertEqual(feedbacks[1].id, f2_id)
        self.assertEqual(feedbacks[1].rating, 4)
        self.assertEqual(feedbacks[1].comment, "Muy buena respuesta")

    def test_validation_rating_out_of_range(self):
        """Prueba que rating=6 o rating=0 falle con excepción de validación."""
        with self.assertRaises((ValueError, ValidationError)):
            self.eval_manager.add_feedback(
                interaction_id=1,
                rating=6,
                confidence=0.5,
                comment="Invalido"
            )

        with self.assertRaises((ValueError, ValidationError)):
            self.eval_manager.add_feedback(
                interaction_id=1,
                rating=0,
                confidence=0.5,
                comment="Invalido"
            )

    def test_validation_confidence_out_of_range(self):
        """Prueba que confidence=1.5 o confidence=-0.1 falle con excepción de validación."""
        with self.assertRaises((ValueError, ValidationError)):
            self.eval_manager.add_feedback(
                interaction_id=1,
                rating=4,
                confidence=1.5,
                comment="Invalido"
            )

        with self.assertRaises((ValueError, ValidationError)):
            self.eval_manager.add_feedback(
                interaction_id=1,
                rating=4,
                confidence=-0.1,
                comment="Invalido"
            )


if __name__ == "__main__":
    unittest.main()
