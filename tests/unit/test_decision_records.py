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

from codebase_analysis_ai.decision_records import (  # noqa: E402
    decision_record_paths,
    validate_decision_records,
)
from codebase_analysis_ai.documentation_map import DocumentationMap  # noqa: E402


SECTIONS = {
    "context": "Context",
    "decision": "Decision",
    "alternatives": "Alternatives considered",
    "consequences": "Consequences",
    "evidence": "Evidence",
    "links": "Links",
}


def adr_entry(path: str, *, status: str = "accepted", date: str = "2026-01-31", **metadata) -> dict:
    value = {
        "path": path,
        "documentKind": "decision-record",
        "sections": SECTIONS,
        "sourcePatterns": [],
        "sourceHashes": {},
        "relatedDocuments": [],
        "metadata": {"status": status, "date": date, **metadata},
    }
    return value


def write_adr(root: Path, number: str, slug: str, *, title: str | None = None) -> str:
    path = f"docs/decisions/ADR-{number}-{slug}.md"
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    heading = title if title is not None else f"ADR-{number}: Decision {number}"
    file.write_text(
        f"# {heading}\n\n"
        "<!-- codebase-analysis-ai:scope:start -->\n"
        "Registra una decisione architetturale durevole.\n"
        "<!-- codebase-analysis-ai:scope:end -->\n\n"
        "## Context\n\nContesto.\n\n"
        "## Decision\n\nDecisione.\n\n"
        "## Alternatives considered\n\nAlternative.\n\n"
        "## Consequences\n\nConseguenze.\n\n"
        "## Evidence\n\nEvidenza.\n\n"
        "## Links\n\nCollegamenti.\n",
        encoding="utf-8",
    )
    return path


def build_map(documents: dict) -> DocumentationMap:
    return DocumentationMap(Path("docs/_meta/documentation-map.json"), {
        "schemaVersion": 1,
        "settings": {},
        "documents": documents,
    })


def write_indexes(root: Path, adr_paths: list[str]) -> None:
    index = root / "docs" / "decisions" / "index.md"
    index.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Decision records\n", "## What this index covers\n\nIndice.\n", "## Accepted\n"]
    for path in adr_paths:
        lines.append(f"- [{path}]({path.rsplit('/', 1)[-1]})")
    lines.append("\n## Related documentation\n\nNessun collegamento.\n")
    index.write_text("\n".join(lines), encoding="utf-8")
    (root / "docs" / "index.md").write_text(
        "# Documentation\n\n[Decision records](decisions/index.md)\n",
        encoding="utf-8",
    )


class DecisionRecordsTest(unittest.TestCase):
    def test_valid_decision_record_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_adr(root, "0001", "authentication")
            write_indexes(root, [path])
            documentation_map = build_map({"adr": adr_entry(path)})

            self.assertEqual([], validate_decision_records(root, documentation_map))

    def test_rejects_duplicate_number_and_incoherent_title(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = write_adr(root, "0001", "first")
            second = write_adr(root, "0001", "second", title="ADR-0002: Second")
            write_indexes(root, [first, second])
            documentation_map = build_map({
                "first": adr_entry(first),
                "second": adr_entry(second),
            })

            errors = validate_decision_records(root, documentation_map)

            self.assertTrue(any("Duplicate ADR number 0001" in error for error in errors))
            self.assertTrue(any("does not match filename" in error for error in errors))

    def test_rejects_invalid_status_date_sections_and_source_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_adr(root, "0001", "decision")
            write_indexes(root, [path])
            entry = adr_entry(path, status="unknown", date="31-01-2026")
            entry["sections"] = {"context": "Context"}
            entry["sourceHashes"] = {"src/app.py": "hash"}
            documentation_map = build_map({"adr": entry})

            errors = validate_decision_records(root, documentation_map)

            self.assertTrue(any("status must be one of" in error for error in errors))
            self.assertTrue(any("date must use YYYY-MM-DD" in error for error in errors))
            self.assertTrue(any("missing sections" in error for error in errors))
            self.assertTrue(any("must not record sourceHashes" in error for error in errors))

    def test_requires_index_link_and_documentation_index_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_adr(root, "0001", "decision")
            (root / "docs" / "decisions" / "index.md").write_text(
                "# Decision records\n", encoding="utf-8"
            )
            (root / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            documentation_map = build_map({"adr": adr_entry(path)})

            errors = validate_decision_records(root, documentation_map)

            self.assertTrue(any("does not link this record" in error for error in errors))
            self.assertTrue(any("documentation index does not link" in error for error in errors))

    def test_accepts_valid_supersession_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = write_adr(root, "0001", "old")
            new = write_adr(root, "0002", "new")
            write_indexes(root, [old, new])
            documentation_map = build_map({
                "old": adr_entry(old, status="superseded", supersededBy="ADR-0002"),
                "new": adr_entry(new, status="accepted", supersedes=["ADR-0001"]),
            })

            self.assertEqual([], validate_decision_records(root, documentation_map))

    def test_rejects_incomplete_supersession_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = write_adr(root, "0001", "old")
            new = write_adr(root, "0002", "new")
            write_indexes(root, [old, new])
            documentation_map = build_map({
                "old": adr_entry(old, status="superseded"),
                "new": adr_entry(new, status="accepted", supersedes=["ADR-0001"]),
            })

            errors = validate_decision_records(root, documentation_map)

            self.assertTrue(any("requires metadata.supersededBy" in error for error in errors))
            self.assertTrue(any("supersededBy pointing to" in error for error in errors))

    def test_recognizes_legacy_adr_directory_without_renaming(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = "docs/adr/ADR-0001-legacy.md"
            file = root / path
            file.parent.mkdir(parents=True)
            file.write_text("# ADR-0001: Legacy\n", encoding="utf-8")
            documentation_map = build_map({"legacy": {
                "path": path,
                "sourcePatterns": [],
                "sourceHashes": {},
                "relatedDocuments": [],
            }})

            self.assertIn(path, decision_record_paths(documentation_map))
            self.assertEqual([], validate_decision_records(root, documentation_map))

    def test_refresh_never_updates_decision_record_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            adr = write_adr(root, "0001", "decision")
            map_path = root / "docs" / "_meta" / "documentation-map.json"
            map_path.parent.mkdir(parents=True)
            map_path.write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {"adr": adr_entry(adr)},
            }), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CLI), "--root", str(root), "refresh", "src/app.py"],
                capture_output=True, text=True, check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            refreshed = json.loads(map_path.read_text(encoding="utf-8"))
            self.assertEqual({}, refreshed["documents"]["adr"]["sourceHashes"])

    def test_validate_docs_reports_adr_errors_and_honors_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            path = write_adr(root, "0001", "decision")
            map_path = root / "docs" / "_meta" / "documentation-map.json"
            map_path.parent.mkdir(parents=True)
            map_path.write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {"adr": adr_entry(path, status="superseded")},
            }), encoding="utf-8")

            relaxed = subprocess.run(
                [sys.executable, str(CLI), "--root", str(root), "validate-docs"],
                capture_output=True, text=True, check=False,
            )
            strict = subprocess.run(
                [sys.executable, str(CLI), "--root", str(root), "validate-docs", "--strict"],
                capture_output=True, text=True, check=False,
            )

            self.assertEqual(0, relaxed.returncode, relaxed.stderr)
            self.assertTrue(json.loads(relaxed.stdout)["adrErrors"])
            self.assertEqual(1, strict.returncode)

    def test_rejects_superseded_status_without_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_adr(root, "0001", "old")
            write_indexes(root, [path])
            documentation_map = build_map({"old": adr_entry(path, status="superseded")})

            errors = validate_decision_records(root, documentation_map)

            self.assertTrue(any("requires metadata.supersededBy" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
