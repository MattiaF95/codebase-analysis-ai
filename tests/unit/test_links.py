import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.link_validator import validate_links  # noqa: E402


class LinkValidatorTest(unittest.TestCase):
    def test_validates_relative_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "target.md").write_text("# Target\n", encoding="utf-8")
            (root / "docs" / "source.md").write_text("[Target](target.md)\n", encoding="utf-8")
            self.assertEqual([], validate_links(root, ["docs/source.md"]))

    def test_reports_broken_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "source.md").write_text("[Missing](missing.md)\n", encoding="utf-8")
            errors = validate_links(root, ["docs/source.md"])
            self.assertEqual(1, len(errors))


if __name__ == "__main__":
    unittest.main()

