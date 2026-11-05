from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))
CLI = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"

from codebase_analysis_ai.documentation_map import DocumentationMap  # noqa: E402
from codebase_analysis_ai.planvault import (  # noqa: E402
    detect_planvault_plans,
    validate_planvault_links,
)


SECTIONS = {
    "context": "Context",
    "decision": "Decision",
    "alternatives": "Alternatives considered",
    "consequences": "Consequences",
    "evidence": "Evidence",
    "links": "Links",
}


def build_map(documents: dict) -> DocumentationMap:
    return DocumentationMap(Path("docs/_meta/documentation-map.json"), {
        "schemaVersion": 1,
        "settings": {},
        "documents": documents,
    })


def adr_entry(path: str, related_plans: list[str] | None = None) -> dict:
    metadata = {"status": "accepted", "date": "2026-01-31"}
    if related_plans is not None:
        metadata["relatedPlans"] = related_plans
    return {
        "path": path,
        "documentKind": "decision-record",
        "sections": SECTIONS,
        "sourcePatterns": [],
        "sourceHashes": {},
        "relatedDocuments": [],
        "metadata": metadata,
    }


def write_adr(root: Path, path: str) -> None:
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        "# ADR-0001: Decision\n\n"
        "<!-- codebase-analysis-ai:scope:start -->\n"
        "Rationale.\n"
        "<!-- codebase-analysis-ai:scope:end -->\n",
        encoding="utf-8",
    )


def write_plan(root: Path, relative: str, body: str) -> None:
    file = root / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(body, encoding="utf-8")


class PlanVaultTest(unittest.TestCase):
    def test_absent_planvault_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_adr(root, "docs/decisions/ADR-0001-decision.md")
            documentation_map = build_map({
                "adr": adr_entry("docs/decisions/ADR-0001-decision.md"),
            })

            self.assertEqual([], detect_planvault_plans(root))
            self.assertEqual([], validate_planvault_links(root, documentation_map))

    def test_detects_single_file_and_three_core_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(root, "plans/single.md", "# Single plan\n")
            write_plan(root, "plans/feature/spec.md", "# Spec\n")
            write_plan(root, "plans/feature/plan.md", "# Plan\n")
            write_plan(root, "plans/feature/tasks.md", "# Tasks\n")

            artifacts = detect_planvault_plans(root)

            self.assertEqual(
                [
                    {"kind": "single-file", "directory": "plans", "files": ["plans/single.md"]},
                    {
                        "kind": "three-core",
                        "directory": "plans/feature",
                        "files": [
                            "plans/feature/spec.md",
                            "plans/feature/plan.md",
                            "plans/feature/tasks.md",
                        ],
                    },
                ],
                artifacts,
            )

    def test_three_core_files_are_not_double_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("spec.md", "plan.md", "tasks.md", "notes.md"):
                write_plan(root, f"plans/feature/{name}", "# Content\n")

            artifacts = detect_planvault_plans(root)

            # Every Markdown file in a three-core directory belongs to that plan,
            # so it is not reported again as an independent single-file plan.
            self.assertEqual([], [path for artifact in artifacts for path in artifact["files"] if path.endswith("notes.md")])
            self.assertEqual(1, sum(1 for artifact in artifacts if artifact["kind"] == "three-core"))

    def test_bidirectional_links_are_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adr = "docs/decisions/ADR-0001-decision.md"
            write_adr(root, adr)
            write_plan(
                root,
                "plans/auth.md",
                "# Plan\n\nConfirmed by [ADR-0001](../docs/decisions/ADR-0001-decision.md).\n",
            )
            documentation_map = build_map({"adr": adr_entry(adr, ["plans/auth.md"])})

            self.assertEqual([], validate_planvault_links(root, documentation_map))

    def test_link_without_related_plans_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adr = "docs/decisions/ADR-0001-decision.md"
            write_adr(root, adr)
            write_plan(
                root,
                "plans/auth.md",
                "# Plan\n\n[ADR](../docs/decisions/ADR-0001-decision.md)\n",
            )
            documentation_map = build_map({"adr": adr_entry(adr)})

            errors = validate_planvault_links(root, documentation_map)

            self.assertTrue(any("does not list this plan" in error for error in errors))

    def test_broken_link_and_unregistered_adr_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_plan(
                root,
                "plans/missing.md",
                "# Plan\n\n[Missing](../docs/decisions/ADR-0002-missing.md)\n",
            )
            documentation_map = build_map({})

            errors = validate_planvault_links(root, documentation_map)

            self.assertTrue(any("broken link to decision record" in error for error in errors))

            write_adr(root, "docs/decisions/ADR-0002-missing.md")
            errors = validate_planvault_links(root, documentation_map)
            self.assertTrue(any("not registered" in error for error in errors))

    def test_plan_completion_does_not_change_adr_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adr = "docs/decisions/ADR-0001-decision.md"
            write_adr(root, adr)
            write_plan(root, "plans/auth.md", "# Plan\n\nDone.\n")
            documentation_map = build_map({"adr": adr_entry(adr, ["plans/auth.md"])})

            validate_planvault_links(root, documentation_map)

            metadata = documentation_map.documents["adr"]["metadata"]
            self.assertEqual("accepted", metadata["status"])
            self.assertEqual(["plans/auth.md"], metadata["relatedPlans"])

    def test_cli_reports_detection_and_honors_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "docs" / "_meta").mkdir(parents=True)
            adr = "docs/decisions/ADR-0001-decision.md"
            write_adr(root, adr)
            write_plan(
                root,
                "plans/auth.md",
                "# Plan\n\n[ADR](../docs/decisions/ADR-0001-decision.md)\n",
            )
            (root / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {"adr": adr_entry(adr)},
            }), encoding="utf-8")

            relaxed = subprocess.run(
                [sys.executable, str(CLI), "--root", str(root), "planvault"],
                capture_output=True, text=True, check=False,
            )
            strict = subprocess.run(
                [sys.executable, str(CLI), "--root", str(root), "planvault", "--strict"],
                capture_output=True, text=True, check=False,
            )

            self.assertEqual(0, relaxed.returncode, relaxed.stderr)
            report = json.loads(relaxed.stdout)
            self.assertTrue(report["detected"])
            self.assertTrue(report["planvaultErrors"])
            self.assertEqual(1, strict.returncode)


if __name__ == "__main__":
    unittest.main()
