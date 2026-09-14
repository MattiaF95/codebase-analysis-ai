import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill" / "codebase-analysis-ai"


class AutomationAssetsTest(unittest.TestCase):
    def test_hooks_emit_json_reports(self):
        for name in ("post-commit", "pre-push", "post-merge", "post-rewrite"):
            content = (SKILL / "assets" / "hooks" / name).read_text(encoding="utf-8")
            self.assertIn("--json", content, name)

    def test_workflow_is_always_warning_only(self):
        content = (SKILL / "assets" / "workflows" / "codebase-analysis-ai.yml").read_text(encoding="utf-8")
        self.assertIn("Documentation audit", content)
        self.assertIn("--warn-only", content)
        self.assertNotIn("forced_push", content)
        self.assertNotIn("if [", content)

    def test_agent_adapters_preserve_hook_context(self):
        adapters = (
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            "copilot-instructions.md",
        )
        for name in adapters:
            content = (SKILL / "assets" / "adapters" / name).read_text(encoding="utf-8")
            self.assertIn("authoritative context", content, name)
            self.assertNotIn("check --mode working-tree --json", content, name)

    def test_documentation_index_template_uses_metadata_coverage_path(self):
        content = (SKILL / "assets" / "templates" / "docs-index.md").read_text(encoding="utf-8")
        self.assertIn("](_meta/coverage.md)", content)
        self.assertNotIn("](coverage.md)", content)

if __name__ == "__main__":
    unittest.main()
