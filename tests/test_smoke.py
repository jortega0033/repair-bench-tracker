import importlib
import subprocess
import sys
import unittest

MODULES = ["contracts", "store", "jobs", "parts", "commands", "reports", "check", "server"]


def run(*args):
    return subprocess.run([sys.executable, "-m", "repair_bench", *args], capture_output=True, text=True)


class SmokeTest(unittest.TestCase):
    def test_modules_import(self):
        for name in MODULES:
            with self.subTest(module=name):
                importlib.import_module(f"repair_bench.{name}")

    def test_expected_stub_imports(self):
        importlib.import_module("tests.expected")

    def test_help_and_version(self):
        self.assertEqual(run("--help").returncode, 0)
        out = run("--version")
        self.assertEqual(out.returncode, 0)
        self.assertIn("repair_bench", out.stdout)

    def test_unbuilt_command_exits_non_zero(self):
        out = run("check", "--data-dir", "x")
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("not implemented yet: see #5", out.stderr)


if __name__ == "__main__":
    unittest.main()
