import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.documentation_map import (  # noqa: E402
    DocumentationMap,
    active_document_paths,
    documentation_issues,
    load_map,
)


class DocumentationMapTest(unittest.TestCase):
    @staticmethod
    def _write_map(root: Path, documents: dict) -> Path:
        map_path = root / "docs" / "_meta" / "documentation-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps({
            "schemaVersion": 1,
            "settings": {},
            "documents": documents,
        }), encoding="utf-8")
        return map_path

    def test_loads_legacy_map_without_new_coverage_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_map(root, {
                "index": {
                    "path": "docs/index.md",
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            })
            (root / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")

            documentation_map = load_map(root)

            self.assertEqual([], documentation_map.validate())
            self.assertEqual([], list(documentation_issues(root, documentation_map).errors))

    def test_active_documents_exempt_metadata_archives_and_non_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs" / "_meta").mkdir(parents=True)
            (root / "docs" / "_archive").mkdir(parents=True)
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "docs" / "_meta" / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (root / "docs" / "_archive" / "old.md").write_text("# Old\n", encoding="utf-8")
            (root / "docs" / "diagram.txt").write_text("diagram\n", encoding="utf-8")

            self.assertEqual(
                ["docs/guide.md", "docs/index.md"],
                active_document_paths(root),
            )

    def test_reports_missing_unregistered_and_index_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "guide": {
                        "path": "docs/guide.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            })
            (root / "docs").mkdir()
            (root / "docs" / "orphan.md").write_text("# Orphan\n", encoding="utf-8")

            issues = documentation_issues(root, documentation_map)

            self.assertIn("docs/guide.md", issues.missing)
            self.assertIn("docs/orphan.md", issues.unregistered)
            self.assertIn("Missing documentation index: docs/index.md", issues.index)
            self.assertIn("Missing document: docs/guide.md", issues.errors)
            self.assertIn("Unregistered document: docs/orphan.md", issues.errors)

    def test_reports_unregistered_existing_index_separately_from_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {},
            })
            (root / "docs").mkdir()
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")

            issues = documentation_issues(root, documentation_map)

            self.assertIn("Unregistered documentation index: docs/index.md", issues.index)
            self.assertNotIn("docs/index.md", issues.unregistered)


if __name__ == "__main__":
    unittest.main()
