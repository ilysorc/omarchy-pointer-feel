import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/install-local.py"
spec = importlib.util.spec_from_file_location("local_installer", path)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class Installation(unittest.TestCase):
    def test_preserves_unrelated_input_and_is_idempotent(self):
        original = 'hl.config({ input = { sensitivity = 0.2 } })\n'
        result = installer.input_config(original)
        self.assertTrue(result.startswith(original))
        self.assertEqual(installer.input_config(result), result)

    def test_fresh_startup_is_vendor_independent_and_idempotent(self):
        original = 'o.launch_on_start("my-personal-service")\n'
        result = installer.startup_config(original, Path("/home/tester"))
        self.assertTrue(result.startswith(original))
        self.assertIn('/home/tester/.local/bin/pointer-feel restore', result)
        self.assertEqual(installer.startup_config(result, Path("/home/tester")), result)

    def test_adopts_existing_windows_startup_without_duplicate_load(self):
        original = 'o.launch_on_start("/home/tester/.local/bin/windows-pointer on")\n'
        result = installer.startup_config(original, Path("/home/tester"))
        self.assertNotIn('windows-pointer on', result)
        self.assertEqual(result.count('pointer-feel restore'), 1)

    def test_duplicate_startup_owners_are_rejected(self):
        original = 'o.launch_on_start("windows-pointer on")\no.launch_on_start("windows-pointer on")\n'
        with self.assertRaises(installer.ControlError):
            installer.startup_config(original, Path("/home/tester"))
