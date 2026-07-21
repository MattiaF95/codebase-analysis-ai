import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.project_installer import install_project_components  # noqa: E402
from codebase_analysis_ai.setup_state import inspect_setup  # noqa: E402


class SetupStateTest(unittest.TestCase):
    def test_reports_missing_setup_and_unindexed_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            state = inspect_setup(root, ["codex"])
            self.assertEqual("absent", state["runtime"])
            self.assertEqual("absent", state["adapters"]["codex"])
            self.assertEqual("not-indexed", state["documentation"]["state"])

    def test_reports_managed_runtime_adapter_and_optional_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            runtime = root / "tools" / "codebase-analysis-ai"
            runtime.mkdir(parents=True)
            (runtime / "check.py").write_text("# runtime\n", encoding="utf-8")
            (root / "AGENTS.md").write_text(
                "<!-- codebase-analysis-ai:start -->\nsetup-state --agents codex\n", encoding="utf-8"
            )
            state = inspect_setup(root, ["codex"])
            self.assertEqual("unmanaged", state["runtime"])
            self.assertEqual("outdated", state["adapters"]["codex"])
            self.assertEqual("absent", state["hooks"]["post-commit"])
            self.assertEqual("absent", state["githubAction"])

    def test_reports_outdated_and_current_managed_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_components(root, ["codex"], False, False, False)
            self.assertEqual("managed", inspect_setup(root, ["codex"])["runtime"])

            module = root / "tools" / "codebase-analysis-ai" / "codebase_analysis_ai" / "source_hashes.py"
            module.write_text("outdated\n", encoding="utf-8")
            self.assertEqual("outdated", inspect_setup(root, ["codex"])["runtime"])

    def test_reports_current_managed_automation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            install_project_components(root, ["codex"], True, True, True)

            state = inspect_setup(root, ["codex"])

            self.assertEqual("managed", state["runtime"])
            self.assertEqual("managed", state["adapters"]["codex"])
            self.assertTrue(all(value == "managed" for value in state["hooks"].values()))
            self.assertEqual("managed", state["githubAction"])

    def test_cli_returns_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            script = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"
            result = subprocess.run(
                [sys.executable, str(script), "--root", str(root), "setup-state", "--agents", "all"],
                check=True, capture_output=True, text=True,
            )
            state = json.loads(result.stdout)
            self.assertEqual("absent", state["runtime"])
            self.assertEqual(4, len(state["adapters"]))


if __name__ == "__main__":
    unittest.main()
