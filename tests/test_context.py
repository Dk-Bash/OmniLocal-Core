import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from context.manager import ContextManager
from context.models import ContextSession, ContextMessage


class TestContextEngine(unittest.TestCase):
    def setUp(self):
        # Crear base de datos temporal para no afectar producción
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.context_manager = ContextManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_session(self):
        """Prueba la creación de una sesión de contexto y verifica la devolución de un ID válido."""
        session_id = self.context_manager.create_session("Proyecto OmniLocal")
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, int)
        self.assertGreater(session_id, 0)

        session = self.context_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.session_name, "Proyecto OmniLocal")
        self.assertTrue(session.active)

    def test_add_and_retrieve_messages(self):
        """Prueba agregar mensajes y recuperar el historial reciente."""
        session_id = self.context_manager.create_session("Aprendizaje Python")

        # Agregar mensaje de usuario
        msg1_id = self.context_manager.add_message(session_id, "user", "Hola")
        self.assertIsNotNone(msg1_id)
        self.assertGreater(msg1_id, 0)

        # Agregar mensaje de asistente
        msg2_id = self.context_manager.add_message(session_id, "assistant", "Hola, ¿cómo estás?")
        self.assertIsNotNone(msg2_id)
        self.assertGreater(msg2_id, 0)

        # Recuperar historial de mensajes
        messages = self.context_manager.get_recent_messages(session_id, limit=10)
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], ContextMessage)
        self.assertIsInstance(messages[1], ContextMessage)

        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hola")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "Hola, ¿cómo estás?")

    def test_close_session(self):
        """Prueba cerrar una sesión cambiando su estado active a False."""
        session_id = self.context_manager.create_session("Sesión Temporal")

        session_before = self.context_manager.get_session(session_id)
        self.assertTrue(session_before.active)

        success = self.context_manager.close_session(session_id)
        self.assertTrue(success)

        session_after = self.context_manager.get_session(session_id)
        self.assertFalse(session_after.active)


if __name__ == "__main__":
    unittest.main()
