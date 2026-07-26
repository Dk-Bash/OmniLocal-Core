import os
import unittest
import tempfile
from database.sqlite_manager import SQLiteManager
from user.manager import UserManager
from user.models import UserProfile, UserPreference


class TestUserProfile(unittest.TestCase):
    def setUp(self):
        # Crear base de datos temporal para aislar las pruebas de producción
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.user_manager = UserManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_profile(self):
        """Prueba la creación de un perfil de usuario y verifica la devolución de un ID válido."""
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")
        self.assertIsNotNone(user_id)
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0)

    def test_get_profile(self):
        """Prueba recuperar un perfil existente por su ID."""
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")
        profile = self.user_manager.get_profile(user_id)

        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.username, "marcelo")
        self.assertEqual(profile.display_name, "Marcelo")
        self.assertEqual(profile.language, "es")

    def test_update_profile(self):
        """Prueba actualizar el nombre e idioma de un perfil de usuario (ej. 'es' -> 'en')."""
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")

        # Actualizar idioma a 'en' y display_name a 'Marcelo K'
        success = self.user_manager.update_profile(user_id, display_name="Marcelo K", language="en")
        self.assertTrue(success)

        updated_profile = self.user_manager.get_profile(user_id)
        self.assertIsNotNone(updated_profile)
        self.assertEqual(updated_profile.display_name, "Marcelo K")
        self.assertEqual(updated_profile.language, "en")

    def test_preferences(self):
        """Prueba guardar y recuperar preferencias de un usuario."""
        user_id = self.user_manager.create_profile("marcelo", "Marcelo", "es")

        # Guardar preferencia response_style = detailed
        pref_id = self.user_manager.set_preference(user_id, "response_style", "detailed")
        self.assertIsNotNone(pref_id)
        self.assertGreater(pref_id, 0)

        # Guardar otra preferencia theme = dark
        pref_id2 = self.user_manager.set_preference(user_id, "theme", "dark")
        self.assertIsNotNone(pref_id2)

        # Recuperar preferencias
        prefs = self.user_manager.get_preferences(user_id)
        self.assertEqual(len(prefs), 2)
        self.assertTrue(all(isinstance(p, UserPreference) for p in prefs))

        keys_values = {p.key: p.value for p in prefs}
        self.assertIn("response_style", keys_values)
        self.assertEqual(keys_values["response_style"], "detailed")
        self.assertIn("theme", keys_values)
        self.assertEqual(keys_values["theme"], "dark")


if __name__ == "__main__":
    unittest.main()
