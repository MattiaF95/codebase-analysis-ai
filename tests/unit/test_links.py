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

    def test_supports_reference_links_nested_parentheses_and_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "flusso (utente).md").write_text("# Target\n", encoding="utf-8")
            (docs / "source.md").write_text(
                "[Flusso][utente]\n[Diretto](flusso%20(utente).md)\n\n"
                "[utente]: <flusso%20(utente).md>\n",
                encoding="utf-8",
            )

            self.assertEqual([], validate_links(root, ["docs/source.md"]))

    def test_ignores_links_in_code_and_images_but_validates_reference_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "source.md").write_text(
                "`[inline](missing-inline.md)`\n"
                "```markdown\n[fenced](missing-fenced.md)\n```\n"
                "![image](missing-image.png)\n"
                "[Missing][reference]\n\n[reference]: missing-reference.md\n",
                encoding="utf-8",
            )

            errors = validate_links(root, ["docs/source.md"])

            self.assertEqual(1, len(errors))
            self.assertIn("missing-reference.md", errors[0])


if __name__ == "__main__":
    unittest.main()
