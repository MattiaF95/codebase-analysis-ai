import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.document_validator import validate_documents  # noqa: E402


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
            self.assertTrue(any("path escapes repository" in issue for issue in report["issues"]))
