import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill" / "codebase-analysis-ai"


class AutomationAssetsTest(unittest.TestCase):
    def test_hooks_emit_json_reports(self):
        for name in ("post-commit", "pre-push", "post-merge", "post-rewrite"):
            content = (SKILL / "assets" / "hooks" / name).read_text(encoding="utf-8")
            self.assertIn("--json", content, name)

    def test_workflow_is_warning_only_and_annotates_only_incoherent_reports(self):
        content = (SKILL / "assets" / "workflows" / "codebase-analysis-ai.yml").read_text(encoding="utf-8")
        self.assertIn("Documentation audit", content)
        self.assertIn("--warn-only", content)
        self.assertNotIn("forced_push", content)
        self.assertNotIn("if [", content)
        self.assertNotIn('echo "::warning', content)
        self.assertIn("json.load", content)
        self.assertIn("if problems:", content)
        for key in (
            "errors",
            "mapErrors",
            "linkErrors",
            "staleMappings",
            "unmappedFiles",
            "missingDocuments",
            "unregisteredDocuments",
            "indexErrors",
            "removedMappings",
        ):
            self.assertIn(f'"{key}"', content)

    def test_pre_push_reports_the_check_outcome_without_assuming_stale_hashes(self):
        content = (SKILL / "assets" / "hooks" / "pre-push").read_text(encoding="utf-8")
        self.assertIn("documentation check reported one or more errors", content)
        self.assertNotIn("documentation hashes do not match", content)
        self.assertIn("git push --no-verify", content)

    def test_repository_ci_runs_the_suite_on_supported_python_versions(self):
        workflow = ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(workflow.is_file())
        content = workflow.read_text(encoding="utf-8")
        self.assertIn("push:", content)
        self.assertIn("pull_request:", content)
        self.assertIn('"3.9"', content)
        self.assertIn('"3.12"', content)
        self.assertIn('python3 -m unittest discover -s tests -p "test_*.py"', content)

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

    def test_agent_adapters_cover_document_kinds_and_decisions(self):
        adapters = (
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            "copilot-instructions.md",
        )
        for name in adapters:
            content = (SKILL / "assets" / "adapters" / name).read_text(encoding="utf-8")
            self.assertIn("documentKind", content, name)
            self.assertIn("docs/decisions/", content, name)
            self.assertIn("docs/_analysis/", content, name)
            self.assertIn("PlanVault", content, name)

    def test_analyzer_contract_reports_kinds_and_decision_candidates(self):
        contract = (SKILL / "references" / "subagent-contract.md").read_text(encoding="utf-8")
        self.assertIn('"documentKind"', contract)
        self.assertIn("decisionCandidates", contract)
        self.assertIn("do not create or modify documentation", contract)

        policy = (SKILL / "references" / "analyzer-profile-policy.md").read_text(encoding="utf-8")
        self.assertIn("document kinds", policy)
        self.assertIn("decision candidates", policy)

        for name in ("host-codex.md", "host-claude.md", "host-gemini.md", "host-copilot.md"):
            content = (SKILL / "references" / name).read_text(encoding="utf-8")
            self.assertIn("decision candidates", content, name)
            self.assertIn("do not create or modify documentation", content, name)

    def test_openai_agent_manifest_mentions_decision_records(self):
        content = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("decision records", content)

    def test_documentation_index_template_uses_metadata_coverage_path(self):
        content = (SKILL / "assets" / "templates" / "docs-index.md").read_text(encoding="utf-8")
        self.assertIn("](_meta/coverage.md)", content)
        self.assertNotIn("](coverage.md)", content)
        self.assertIn("Cross-cutting documentation", content)

    def test_templates_cover_analysis_reports_coverage_and_kind_indexes(self):
        templates = SKILL / "assets" / "templates"
        for name in ("coverage.md", "analysis-report.md", "kind-index.md"):
            with self.subTest(name=name):
                content = (templates / name).read_text(encoding="utf-8")
                self.assertIn("codebase-analysis-ai:scope:start", content)

if __name__ == "__main__":
    unittest.main()
