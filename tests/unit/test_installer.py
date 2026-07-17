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

    def test_optional_files_are_not_replaced_when_already_managed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hook = root / ".githooks" / "post-commit"
            hook.parent.mkdir()
            hook.write_text("#!/bin/sh\n# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            action = root / ".github" / "workflows" / "codebase-analysis-ai.yml"
            action.parent.mkdir(parents=True)
            action.write_text("# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            before_hook = hook.read_text(encoding="utf-8")
            before_action = action.read_text(encoding="utf-8")
            install_project_components(root, ["codex"], False, True, True)
            self.assertEqual(before_hook, hook.read_text(encoding="utf-8"))
            self.assertEqual(before_action, action.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
