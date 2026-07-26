import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from retrieval.engine import RetrievalEngine
from user.manager import UserManager
from context.manager import ContextManager
from personalization.engine import PersonalizedRetrievalEngine
from orchestration.engine import OrchestratorEngine
from orchestration.models import InteractionResult


class TestOrchestration(unittest.TestCase):
    def setUp(self):
        # Crear base de datos temporal aislada para pruebas
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()

        self.memory_manager = MemoryManager(db_manager=self.db_manager)
        self.retrieval_engine = RetrievalEngine(memory_manager=self.memory_manager)
        self.user_manager = UserManager(db_manager=self.db_manager)
        self.context_manager = ContextManager(db_manager=self.db_manager)

        self.personalized_engine = PersonalizedRetrievalEngine(
            retrieval_engine=self.retrieval_engine,
            user_manager=self.user_manager,
            context_manager=self.context_manager
        )

        self.orchestrator = OrchestratorEngine(
            personalized_engine=self.personalized_engine,
            context_manager=self.context_manager,
            memory_manager=self.memory_manager
        )

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_basic_interaction(self):
        """Prueba de interacción básica sin usuario ni sesión."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.8)

        res = self.orchestrator.process_interaction("Python")

        self.assertIsInstance(res, InteractionResult)
        self.assertEqual(res.query, "Python")
        self.assertGreater(res.results_count, 0)
        self.assertIsNotNone(res.id)

    def test_interaction_with_context(self):
        """Prueba de interacción en una sesión conversacional activa."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.8)

        # Crear sesión
        session_id = self.context_manager.create_session("Aprendizaje Python")

        # Procesar interacción con sesión
        res = self.orchestrator.process_interaction("Estoy estudiando Python", session_id=session_id)

        # Verificar resultado e historial en el ContextManager
        self.assertIsInstance(res, InteractionResult)
        messages = self.context_manager.get_recent_messages(session_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "Estoy estudiando Python")
        self.assertEqual(messages[0].role, "user")

    def test_personalized_interaction(self):
        """Prueba de interacción personalizada para un usuario con preferencias."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.8)

        # Crear usuario y guardar preferencia
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")
        self.user_manager.set_preference(user_id, "response_style", "detailed")

        # Procesar interacción con user_id
        res = self.orchestrator.process_interaction("Python", user_id=user_id)

        self.assertIsInstance(res, InteractionResult)
        self.assertGreater(res.results_count, 0)


if __name__ == "__main__":
    unittest.main()
