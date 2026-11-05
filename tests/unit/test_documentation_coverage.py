import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.documentation_coverage import (  # noqa: E402
    coverage_counts,
    coverage_markdown,
    navigation_issues,
)
from codebase_analysis_ai.documentation_map import DocumentationMap  # noqa: E402


def mapping(documents: dict) -> DocumentationMap:
    return DocumentationMap(Path("docs/_meta/documentation-map.json"), {
        "schemaVersion": 1,
        "settings": {},
        "documents": documents,
    })


class DocumentationCoverageTest(unittest.TestCase):
    def test_counts_documents_by_kind_and_decision_status(self):
        documentation_map = mapping({
            "index": {"path": "docs/index.md", "documentKind": "documentation-index"},
            "area": {"path": "docs/backend/README.md", "documentKind": "area"},
            "topic": {"path": "docs/backend/auth.md", "documentKind": "topic"},
            "adr-1": {
                "path": "docs/decisions/ADR-0001-auth.md",
                "documentKind": "decision-record",
                "metadata": {"status": "accepted"},
            },
            "adr-2": {
                "path": "docs/decisions/ADR-0002-session.md",
                "documentKind": "decision-record",
                "metadata": {"status": "superseded"},
            },
            "legacy": {"path": "docs/legacy.md"},
        })

        counts = coverage_counts(documentation_map)

        self.assertEqual(6, counts["documents"])
        self.assertEqual(
            {
                "documentation-index": 1,
                "area": 1,
                "topic": 1,
                "decision-record": 2,
                "legacy": 1,
            },
            counts["byKind"],
        )
        self.assertEqual({"accepted": 1, "superseded": 1}, counts["byAdrStatus"])
        self.assertEqual({"indexed": 3, "kind-index": 2, "legacy": 1}, counts["byIndexPolicy"])

    def test_markdown_renders_counts(self):
        markdown = coverage_markdown({
            "documents": 2,
            "byKind": {"area": 1, "decision-record": 1},
            "byAdrStatus": {"accepted": 1},
            "byIndexPolicy": {"indexed": 1, "kind-index": 1},
        })

        self.assertIn("| `area` | 1 |", markdown)
        self.assertIn("| `decision-record` | 1 |", markdown)
        self.assertIn("| `accepted` | 1 |", markdown)

    def test_navigation_is_skipped_for_legacy_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs" / "backend").mkdir(parents=True)
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
            (root / "docs" / "backend" / "index.md").write_text("# Area\n", encoding="utf-8")
            documentation_map = mapping({
                "index": {"path": "docs/index.md"},
                "area": {"path": "docs/backend/index.md", "documentKind": "area"},
            })

            report = navigation_issues(root, documentation_map)

            self.assertEqual([], report["navigationErrors"])
            self.assertEqual([], report["coverageErrors"])

    def test_navigation_requires_area_kind_indexes_and_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            (docs / "backend").mkdir(parents=True)
            (docs / "decisions").mkdir()
            (docs / "_meta").mkdir()
            (docs / "_analysis").mkdir()
            (docs / "index.md").write_text("# Index\n", encoding="utf-8")
            (docs / "backend" / "index.md").write_text("# Area\n", encoding="utf-8")
            (docs / "decisions" / "index.md").write_text("# Decisions\n", encoding="utf-8")
            (docs / "_analysis" / "index.md").write_text("# Analysis\n", encoding="utf-8")
            documentation_map = mapping({
                "index": {"path": "docs/index.md", "documentKind": "documentation-index"},
                "area": {"path": "docs/backend/index.md", "documentKind": "area"},
                "decisions": {"path": "docs/decisions/index.md", "documentKind": "decision-record"},
            })

            report = navigation_issues(root, documentation_map)

            self.assertTrue(any("docs/backend/index.md" in error for error in report["navigationErrors"]))
            self.assertTrue(any("docs/decisions/index.md" in error for error in report["navigationErrors"]))
            self.assertFalse(any("_analysis" in error for error in report["navigationErrors"]))
            self.assertTrue(any("Missing documentation coverage" in error for error in report["coverageErrors"]))

    def test_cli_reports_coverage_as_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "docs" / "_meta").mkdir(parents=True)
            (root / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "area": {"path": "docs/backend/README.md", "documentKind": "area"},
                },
            }), encoding="utf-8")
            script = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"

            report = subprocess.run(
                [sys.executable, str(script), "--root", str(root), "coverage"],
                capture_output=True, text=True, check=False,
            )
            markdown = subprocess.run(
                [sys.executable, str(script), "--root", str(root), "coverage", "--markdown"],
                capture_output=True, text=True, check=False,
            )

            self.assertEqual(0, report.returncode, report.stderr)
            self.assertEqual({"area": 1}, json.loads(report.stdout)["byKind"])
            self.assertEqual(0, markdown.returncode, markdown.stderr)
            self.assertIn("| `area` | 1 |", markdown.stdout)

    def test_navigation_accepts_complete_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            (docs / "backend").mkdir(parents=True)
            (docs / "decisions").mkdir()
            (docs / "_meta").mkdir()
            (docs / "index.md").write_text(
                "# Index\n\n"
                "[Backend](backend/index.md)\n"
                "[Decisions](decisions/index.md)\n"
                "[Coverage](_meta/coverage.md)\n",
                encoding="utf-8",
            )
            (docs / "backend" / "index.md").write_text("# Area\n", encoding="utf-8")
            (docs / "decisions" / "index.md").write_text("# Decisions\n", encoding="utf-8")
            (docs / "_meta" / "coverage.md").write_text("# Coverage\n", encoding="utf-8")
            documentation_map = mapping({
                "index": {"path": "docs/index.md", "documentKind": "documentation-index"},
                "area": {"path": "docs/backend/index.md", "documentKind": "area"},
                "decisions": {"path": "docs/decisions/index.md", "documentKind": "decision-record"},
            })

            report = navigation_issues(root, documentation_map)

            self.assertEqual([], report["navigationErrors"])
            self.assertEqual([], report["coverageErrors"])


if __name__ == "__main__":
    unittest.main()
