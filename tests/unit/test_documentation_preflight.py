import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.documentation_preflight import first_documentation_file  # noqa: E402


class DocumentationPreflightTest(unittest.TestCase):
    def test_returns_first_documentation_path_without_reading_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('code')", encoding="utf-8")
            (root / "notes.pdf").write_bytes(b"not inspected")

            self.assertEqual(first_documentation_file(root), root / "notes.pdf")

    def test_detects_office_files_and_canonical_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "project-plan.pptx").write_bytes(b"not inspected")

            self.assertEqual(first_documentation_file(root), root / "project-plan.pptx")

            (root / "project-plan.pptx").unlink()
            (root / "LICENSE").write_text("license", encoding="utf-8")
            self.assertEqual(first_documentation_file(root), root / "LICENSE")

    def test_ignores_generated_and_dependency_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "README.md").write_text("dependency", encoding="utf-8")

            self.assertIsNone(first_documentation_file(root))


if __name__ == "__main__":
    unittest.main()
