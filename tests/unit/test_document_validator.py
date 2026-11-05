from __future__ import annotations

import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.document_validator import validate_documents  # noqa: E402
from codebase_analysis_ai.documentation_map import DocumentationMap  # noqa: E402


SECTIONS = {
    "coverage": "Cosa copre questo documento",
    "context": "Contesto",
    "responsibilities": "Responsabilità",
    "howItWorks": "Come funziona",
    "activeFunctionality": "Funzionalità attive",
    "relatedDocumentation": "Documentazione correlata",
    "sources": "Fonti",
}


def topic_document(*, omit: str | None = None, duplicate: str | None = None, empty: bool = False) -> str:
    lines = [
        "# Guida",
        "",
        "## Cosa copre questo documento",
        "<!-- codebase-analysis-ai:scope:start -->",
        "Descrive come funziona la guida.",
        "<!-- codebase-analysis-ai:scope:end -->",
    ]
    for key, label in SECTIONS.items():
        if key == "coverage":
            continue
        if key == omit:
            continue
        lines.extend(["", f"## {label}", "Contenuto."])
        if key == duplicate:
            lines.extend(["", f"## {label}", "Duplicato."])
    if empty:
        lines.extend(["", "## ", "Senza titolo."])
    return "\n".join(lines) + "\n"


class DocumentValidatorTest(unittest.TestCase):
    def test_accepts_bounded_scope_and_valid_finding_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "docs" / "flow.md"
            document.parent.mkdir()
            document.write_text(
                "<!-- codebase-analysis-ai:scope:start -->\n"
                "Descrive il flusso di autenticazione e i suoi confini.\n"
                "<!-- codebase-analysis-ai:scope:end -->\n"
                '<!-- codebase-analysis-ai:finding {"kind":"bug","severity":"high","verification":"test"} -->\n',
                encoding="utf-8",
            )

            self.assertTrue(validate_documents(root)["valid"])

    def test_accepts_localized_sections_declared_in_the_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text(topic_document(), encoding="utf-8")
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "guide": {
                        "path": "docs/guide.md",
                        "documentKind": "topic",
                        "sections": SECTIONS,
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            })

            report = validate_documents(root, documentation_map=documentation_map)

            self.assertTrue(report["valid"], report["issues"])

    def test_reports_missing_duplicate_and_empty_section_headings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "missing.md").write_text(topic_document(omit="context"), encoding="utf-8")
            (root / "docs" / "duplicate.md").write_text(topic_document(duplicate="context"), encoding="utf-8")
            (root / "docs" / "empty.md").write_text(topic_document(empty=True), encoding="utf-8")
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    name: {
                        "path": f"docs/{name}.md",
                        "documentKind": "topic",
                        "sections": SECTIONS,
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    }
                    for name in ("missing", "duplicate", "empty")
                },
            })

            issues = validate_documents(root, documentation_map=documentation_map)["issues"]

            self.assertTrue(any("missing declared section 'Contesto' (context)" in issue for issue in issues))
            self.assertTrue(any("duplicate section heading 'Contesto' (context)" in issue for issue in issues))
            self.assertTrue(any("empty second-level heading" in issue for issue in issues))

    def test_documents_without_sections_remain_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "legacy.md").write_text(
                "# Legacy\n\n"
                "<!-- codebase-analysis-ai:scope:start -->\n"
                "Documento legacy senza contratto di sezioni.\n"
                "<!-- codebase-analysis-ai:scope:end -->\n",
                encoding="utf-8",
            )
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "legacy": {
                        "path": "docs/legacy.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            })

            report = validate_documents(root, documentation_map=documentation_map)

            self.assertTrue(report["valid"], report["issues"])

    def test_reports_missing_markers_long_scope_and_invalid_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "legacy.md").write_text("# Legacy\n", encoding="utf-8")
            (docs / "invalid.md").write_text(
                "<!-- codebase-analysis-ai:scope:start -->\n"
                + "parola " * 36
                + "\n<!-- codebase-analysis-ai:scope:end -->\n"
                + '<!-- codebase-analysis-ai:finding {"kind":"other","severity":"high","verification":"test"} -->\n',
                encoding="utf-8",
            )

            issues = validate_documents(root)["issues"]

            self.assertTrue(any("missing managed scope markers" in issue for issue in issues))
            self.assertTrue(any("exceeds 35 words" in issue for issue in issues))
            self.assertTrue(any("unsupported finding kind" in issue for issue in issues))

    def test_cli_is_warn_only_by_default_and_strict_on_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            docs = root / "docs"
            docs.mkdir()
            (docs / "legacy.md").write_text("# Legacy\n", encoding="utf-8")
            script = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"
            command = [sys.executable, str(script), "--root", str(root), "validate-docs"]

            warning = subprocess.run(command, capture_output=True, text=True, check=False)
            strict = subprocess.run([*command, "--strict"], capture_output=True, text=True, check=False)

            self.assertEqual(0, warning.returncode)
            self.assertFalse(json.loads(warning.stdout)["valid"])
            self.assertEqual(1, strict.returncode)

    def test_rejects_explicit_paths_that_escape_repository(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "outside.md"
            external.write_text("# Outside\n", encoding="utf-8")
            requested = external.relative_to(root.parent).as_posix()

            report = validate_documents(root, [f"../{requested}"])

            self.assertFalse(report["valid"])
            self.assertEqual([], report["documents"])
            self.assertTrue(any("path must be repository-relative" in issue for issue in report["issues"]))

    def test_rejects_absolute_paths_even_inside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "docs" / "guide.md"
            document.parent.mkdir()
            document.write_text(
                "<!-- codebase-analysis-ai:scope:start -->\nGuide scope.\n"
                "<!-- codebase-analysis-ai:scope:end -->\n",
                encoding="utf-8",
            )

            report = validate_documents(root, [str(document)])

            self.assertFalse(report["valid"])
            self.assertEqual([], report["documents"])
            self.assertTrue(any("path must be repository-relative" in issue for issue in report["issues"]))
