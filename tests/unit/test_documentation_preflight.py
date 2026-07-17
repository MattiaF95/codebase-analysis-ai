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

    def test_ignores_agent_and_ide_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in (".codex", ".agents", ".vscode", ".idea"):
                path = root / folder / "skill" / "README.md"
                path.parent.mkdir(parents=True)
                path.write_text("tooling", encoding="utf-8")

            self.assertIsNone(first_documentation_file(root))

    def test_ignores_historical_documentation_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archived = root / "docs" / "_archive" / "pre-bootstrap" / "README.md"
            archived.parent.mkdir(parents=True)
            archived.write_text("historical", encoding="utf-8")

            self.assertIsNone(first_documentation_file(root))

    def test_prioritizes_root_readme_as_canonical_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "README.md").write_text("docs", encoding="utf-8")
            (root / "README.md").write_text("project", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "README.md")

    def test_prioritizes_root_readme_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "README.md").write_text("docs", encoding="utf-8")
            (root / "Readme.md").write_text("project", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "Readme.md")


if __name__ == "__main__":
    unittest.main()
