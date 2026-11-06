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
from codebase_analysis_ai.project_detection import (  # noqa: E402
    MAX_STRUCTURAL_FILES,
    inventory_project,
)


class ProjectInventoryTest(unittest.TestCase):
    def test_collects_structure_without_interpreting_project_areas(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            (root / "angular.json").write_text("{}\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(2, result["schemaVersion"])
            self.assertEqual(["README.md", "angular.json", "index.html", "package.json"], result["rootFiles"])
            self.assertNotIn("areas", result)
            self.assertNotIn("documentationTopics", result)
            self.assertNotIn("technologies", result)

    def test_collects_module_roots_and_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = root / "services" / "billing"
            service.mkdir(parents=True)
            (service / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            (service / "README.md").write_text("# Billing\n", encoding="utf-8")
            tests = service / "tests"
            tests.mkdir()
            (tests / "test_api.py").write_text("def test_ok(): pass\n", encoding="utf-8")
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(["services/billing"], result["moduleRoots"])
            self.assertIn("services/billing/pyproject.toml", result["structuralFiles"])
            self.assertEqual(["services/billing/tests/test_api.py"], result["signals"]["tests"])
            self.assertEqual([".github/workflows/ci.yml"], result["signals"]["workflows"])

    def test_keeps_unknown_root_manifest_as_neutral_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "workspace").write_text("modules = []\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(["workspace"], result["rootFiles"])
            self.assertEqual(["workspace"], result["structuralFiles"])

    def test_exposes_unknown_shallow_files_without_classifying_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = root / "custom-module"
            module.mkdir()
            (module / "project.unfamiliar").write_text("module\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(["custom-module/project.unfamiliar"], result["shallowFiles"])
            self.assertEqual([], result["structuralFiles"])

    def test_excludes_agent_metadata_dependencies_and_generated_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in (
                ".agents", "node_modules", "dist", ".venv", "venv", ".tox",
                ".nox", ".pytest_cache", ".mypy_cache", ".ruff_cache", "vendor",
            ):
                path = root / folder
                path.mkdir()
                (path / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(["package.json"], result["structuralFiles"])
            self.assertEqual(1, result["fileCount"])

    def test_excludes_historical_documentation_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archived = root / "docs" / "_archive" / "pre-bootstrap" / "package.json"
            archived.parent.mkdir(parents=True)
            archived.write_text("{}\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(["package.json"], result["structuralFiles"])
            self.assertEqual(1, result["fileCount"])

    def test_excludes_sensitive_paths_from_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("TOKEN=value\n", encoding="utf-8")
            (root / "deploy-secret.pem").write_text("secret\n", encoding="utf-8")
            (root / "README.md").write_text("# Project\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(1, result["fileCount"])
            self.assertEqual([], result["signals"]["deployment"])

    def test_reports_truncation_deterministically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(MAX_STRUCTURAL_FILES + 1):
                module = root / f"module-{index:03d}"
                module.mkdir()
                (module / "package.json").write_text("{}\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(MAX_STRUCTURAL_FILES, len(result["structuralFiles"]))
            self.assertEqual(sorted(result["structuralFiles"]), result["structuralFiles"])
            self.assertTrue(result["truncated"])

    def test_cli_returns_inventory_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
            script = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(root), "detect"],
                check=True,
                capture_output=True,
                text=True,
            )
            inventory = json.loads(result.stdout)

            self.assertEqual(2, inventory["schemaVersion"])
            self.assertEqual(["Cargo.toml"], inventory["structuralFiles"])

    def test_walker_prunes_populated_excluded_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node_modules = root / "node_modules"
            node_modules.mkdir()
            for index in range(200):
                (node_modules / f"package-{index:03d}.json").write_text("{}\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")

            visited = []
            original_walk = os.walk

            def recording_walk(path, **kwargs):
                for dirpath, dirnames, filenames in original_walk(path, **kwargs):
                    visited.append(Path(dirpath))
                    yield dirpath, dirnames, filenames

            with mock.patch.object(path_filters.os, "walk", side_effect=recording_walk):
                result = inventory_project(root)

            self.assertFalse(any("node_modules" in path.parts for path in visited))
            self.assertEqual(2, result["fileCount"])
            self.assertEqual(["package.json"], result["structuralFiles"])

    def test_excludes_additional_generated_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("coverage", "out", "obj", ".next", ".angular"):
                path = root / folder
                path.mkdir()
                (path / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(1, result["fileCount"])
            self.assertEqual(["package.json"], result["structuralFiles"])

    def test_does_not_follow_directory_symlinks(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are not supported")
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            outside_path = Path(outside)
            (outside_path / "package.json").write_text("{}\n", encoding="utf-8")
            try:
                (root / "linked").symlink_to(outside_path, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available")
            (root / "package.json").write_text("{}\n", encoding="utf-8")

            result = inventory_project(root)

            self.assertEqual(1, result["fileCount"])
            self.assertEqual(["package.json"], result["structuralFiles"])


if __name__ == "__main__":
    unittest.main()
