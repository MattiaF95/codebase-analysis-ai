import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.project_installer import START, update_managed_block, install_project_components  # noqa: E402


class InstallerTest(unittest.TestCase):
    def test_managed_block_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            block = f"{START}\nRule one.\n<!-- codebase-analysis-ai:end -->"
            update_managed_block(target, block)
            update_managed_block(target, block)
            content = target.read_text(encoding="utf-8")
            self.assertEqual(1, content.count(START))
            self.assertIn("Keep this.", content)

    def test_existing_automation_is_preserved_and_missing_files_are_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hook = root / ".githooks" / "post-commit"
            hook.parent.mkdir()
            hook.write_text("#!/bin/sh\n# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            hook.chmod(0o600)
            action = root / ".github" / "workflows" / "codebase-analysis-ai.yml"
            action.parent.mkdir(parents=True)
            action.write_text("# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            install_project_components(root, ["codex"], False, True, True)
            self.assertIn("custom", hook.read_text(encoding="utf-8"))
            self.assertEqual(0o600, hook.stat().st_mode & 0o777)
            self.assertIn("custom", action.read_text(encoding="utf-8"))
            self.assertIn("check --mode pre-push", (root / ".githooks" / "pre-push").read_text(encoding="utf-8"))

            second_changes = install_project_components(root, ["codex"], False, True, True)
            self.assertNotIn(".githooks/post-commit", second_changes)
            self.assertNotIn(".github/workflows/codebase-analysis-ai.yml", second_changes)

    def test_agent_file_is_append_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "AGENTS.md"
            target.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            install_project_components(root, ["codex"], True, False, False)
            first = target.read_text(encoding="utf-8")
            self.assertIn("Keep this.", first)
            install_project_components(root, ["codex"], True, False, False)
            self.assertEqual(first, target.read_text(encoding="utf-8"))

    def test_existing_managed_agent_block_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "AGENTS.md"
            target.write_text(
                "# Existing\n\n<!-- codebase-analysis-ai:start -->\nold rule\n"
                "<!-- codebase-analysis-ai:end -->\n\n# Manual\n",
                encoding="utf-8",
            )

            install_project_components(root, ["codex"], True, False, False)

            content = target.read_text(encoding="utf-8")
            self.assertIn("# Existing", content)
            self.assertIn("# Manual", content)
            self.assertIn("Hook interruption protocol", content)
            self.assertNotIn("old rule", content)

    def test_existing_runtime_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "tools" / "codebase-analysis-ai"
            package = runtime / "codebase_analysis_ai"
            package.mkdir(parents=True)
            (runtime / "check.py").write_text("local runtime", encoding="utf-8")
            (package / "custom.py").write_text("local module", encoding="utf-8")

            install_project_components(root, ["codex"], False, False, False)

            self.assertEqual("local runtime", (runtime / "check.py").read_text(encoding="utf-8"))
            self.assertEqual("local module", (package / "custom.py").read_text(encoding="utf-8"))

    def test_existing_hooks_path_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "custom-hooks").mkdir()
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", "custom-hooks"], check=True)

            with self.assertRaisesRegex(RuntimeError, "core.hooksPath"):
                install_project_components(root, ["codex"], False, True, False)
            self.assertFalse((root / "tools" / "codebase-analysis-ai").exists())

    def test_missing_githooks_and_stale_hooks_path_are_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", "missing-hooks"], check=True)

            install_project_components(root, ["codex"], False, True, False)

            self.assertTrue((root / ".githooks" / "pre-push").is_file())
            self.assertEqual(".githooks", subprocess.run(
                ["git", "-C", str(root), "config", "--get", "core.hooksPath"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.strip())


if __name__ == "__main__":
    unittest.main()
