import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from memory.manager import MemoryManager
from retrieval.engine import RetrievalEngine
from user.manager import UserManager
from context.manager import ContextManager
from personalization.engine import PersonalizedRetrievalEngine
from personalization.models import PersonalizedResult


class TestPersonalizedRetrieval(unittest.TestCase):
    def setUp(self):
        # Crear base de datos temporal aislada
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

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_basic_search(self):
        """Prueba búsqueda básica personal de un recuerdo guardado."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.9)

        results = self.personalized_engine.search("Python")
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0], PersonalizedResult)
        self.assertIn("Python", results[0].content)
        self.assertGreaterEqual(results[0].relevance_score, 0.5)

    def test_search_with_user(self):
        """Prueba búsqueda incluyendo datos y preferencias del usuario."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.8)

        # Crear perfil de usuario y preferencia
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")
        self.user_manager.set_preference(user_id, "response_style", "detailed")

        results = self.personalized_engine.search("Python", user_id=user_id)
        self.assertGreater(len(results), 0)
        self.assertIn("preferencias", results[0].reason.lower())

    def test_search_with_context(self):
        """Prueba búsqueda con sesión de contexto activa para aumentar la relevancia del resultado."""
        self.memory_manager.save_memory("Estoy aprendiendo Python", memory_type="learning", importance=0.8)

        # Búsqueda base sin contexto
        base_results = self.personalized_engine.search("Python")
        base_score = base_results[0].relevance_score

        # Crear sesión de contexto y mensaje reciente
        session_id = self.context_manager.create_session("Aprendizaje Python")
        self.context_manager.add_message(session_id, "user", "Estoy estudiando Python con proyectos prácticos")

        # Búsqueda con contexto
        context_results = self.personalized_engine.search("Python", session_id=session_id)
        self.assertGreater(len(context_results), 0)
        self.assertGreaterEqual(context_results[0].relevance_score, base_score)
        self.assertIn("contexto actual", context_results[0].reason.lower())


if __name__ == "__main__":
    unittest.main()
