import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai import path_filters  # noqa: E402
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

    def test_ignores_agent_instruction_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("agent rules", encoding="utf-8")
            (root / "CLAUDE.md").write_text("agent rules", encoding="utf-8")
            (root / ".github" / "copilot-instructions.md").parent.mkdir(parents=True)
            (root / ".github" / "copilot-instructions.md").write_text("agent rules", encoding="utf-8")

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

    def test_source_html_is_not_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "index.html").write_text("<html></html>", encoding="utf-8")

            self.assertIsNone(first_documentation_file(root))

    def test_html_in_documentation_directory_is_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "index.html").write_text("<html></html>", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "index.html").write_text("<html></html>", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "docs" / "index.html")

    def test_root_readme_html_and_txt_are_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.html").write_text("<html></html>", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "README.html")

            (root / "README.html").unlink()
            (root / "README.txt").write_text("project", encoding="utf-8")
            self.assertEqual(first_documentation_file(root), root / "README.txt")

    def test_root_readme_txt_is_prioritized_over_docs_readme(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "README.md").write_text("docs", encoding="utf-8")
            (root / "readme.txt").write_text("project", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "readme.txt")

    def test_text_outside_documentation_directories_is_not_documentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "notes.txt").write_text("notes", encoding="utf-8")

            self.assertIsNone(first_documentation_file(root))

    def test_markdown_counts_in_any_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "notes.md").write_text("# Notes\n", encoding="utf-8")

            self.assertEqual(first_documentation_file(root), root / "src" / "notes.md")

    def test_prunes_populated_excluded_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node_modules = root / "node_modules"
            node_modules.mkdir()
            for index in range(200):
                (node_modules / f"README-{index:03d}.md").write_text("# Dep\n", encoding="utf-8")

            visited = []
            original_walk = os.walk

            def recording_walk(path, **kwargs):
                for dirpath, dirnames, filenames in original_walk(path, **kwargs):
                    visited.append(Path(dirpath))
                    yield dirpath, dirnames, filenames

            with mock.patch.object(path_filters.os, "walk", side_effect=recording_walk):
                self.assertIsNone(first_documentation_file(root))

            self.assertFalse(any("node_modules" in path.parts for path in visited))

    def test_cli_reports_none_for_source_only_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "src").mkdir()
            (root / "src" / "index.html").write_text("<html></html>", encoding="utf-8")
            script = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(root), "docs-state"],
                check=True,
                capture_output=True,
                text=True,
            )
            state = json.loads(result.stdout)

            self.assertEqual("none", state["documentationState"])
            self.assertIsNone(state["firstDocument"])


if __name__ == "__main__":
    unittest.main()
