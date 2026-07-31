import unittest
import tempfile
import os
import json
from database.sqlite_manager import SQLiteManager
from omnilocal_runtime.bindings.models import CapabilityBindingResult
from omnilocal_runtime.bindings.manager import CapabilityBindingManager


class DummyManager:
    """Manager de prueba para verificar bindings."""
    def run_dummy_task(self):
        return {"result": "success_dummy_data", "count": 42}


class TestRuntimeBindings(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_bindings.db")
        self.db_manager = SQLiteManager(db_path=self.db_path)
        self.db_manager.create_tables()
        self.binding_manager = CapabilityBindingManager(db_manager=self.db_manager)

    def tearDown(self):
        self.db_manager.close()
        self.temp_dir.cleanup()

    def test_register_and_get_binding(self):
        dummy = DummyManager()
        self.binding_manager.register_binding(
            stage_name="test_stage",
            manager_or_handler=dummy,
            method_name="run_dummy_task",
        )

        binding = self.binding_manager.get_binding("test_stage")
        self.assertIsNotNone(binding)
        self.assertEqual(binding["manager_name"], "DummyManager")
        self.assertEqual(binding["method_name"], "run_dummy_task")

    def test_execute_binding_and_persistence(self):
        dummy = DummyManager()
        self.binding_manager.register_binding(
            stage_name="test_stage",
            manager_or_handler=dummy,
            method_name="run_dummy_task",
        )

        res = self.binding_manager.execute_binding("test_stage")

        self.assertTrue(res.success)
        self.assertEqual(res.stage_name, "test_stage")
        self.assertEqual(res.manager_name, "DummyManager")
        self.assertIsNotNone(res.id)
        self.assertIn("success_dummy_data", str(res.data))

        # Verificar persistencia en base de datos SQLite
        db_res = self.db_manager.get_capability_result(res.id)
        self.assertIsNotNone(db_res)
        self.assertEqual(db_res["stage_name"], "test_stage")
        self.assertEqual(db_res["manager_name"], "DummyManager")
        self.assertTrue(db_res["success"])

        all_results = self.db_manager.get_capability_results()
        self.assertEqual(len(all_results), 1)

    def test_execute_unregistered_binding_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.binding_manager.execute_binding("non_registered_stage")


if __name__ == "__main__":
    unittest.main()
