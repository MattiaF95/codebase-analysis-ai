import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.todo_scanner import scan_todos  # noqa: E402


class TodoScannerTest(unittest.TestCase):
    def test_ignores_mentions_and_keeps_actionable_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.md"
            report.write_text(
                "No TODO or FIXME markers were found.\n"
                "- TODO: add coverage\n"
                "FIXME update the link\n",
                encoding="utf-8",
            )
            source = root / "service.py"
            source.write_text(
                "# TODO handle retry\n"
                "message = 'No TODO or FIXME markers'\n"
                "return value  # FIXME: validate input\n",
                encoding="utf-8",
            )

            report_findings = scan_todos(root, ["report.md"])
            source_findings = scan_todos(root, ["service.py"])

            self.assertEqual(["TODO", "FIXME"], [item["marker"] for item in report_findings])
            self.assertEqual([1, 3], [item["line"] for item in source_findings])


if __name__ == "__main__":
    unittest.main()
