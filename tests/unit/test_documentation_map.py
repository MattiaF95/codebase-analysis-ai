import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.documentation_map import (  # noqa: E402
    DocumentationMap,
    MapError,
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

    def test_accepts_document_kind_and_localized_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_map(root, {
                "guide": {
                    "path": "docs/guide.md",
                    "documentKind": "topic",
                    "sections": {
                        "coverage": "Cosa copre questo documento",
                        "context": "Contesto",
                        "responsibilities": "Responsabilità",
                        "howItWorks": "Come funziona",
                        "activeFunctionality": "Funzionalità attive",
                        "relatedDocumentation": "Documentazione correlata",
                        "sources": "Fonti",
                    },
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            })

            documentation_map = load_map(root)

            self.assertEqual([], documentation_map.validate())
            self.assertEqual("topic", documentation_map.documents["guide"]["documentKind"])

    def test_rejects_unknown_document_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_map(root, {
                "guide": {
                    "path": "docs/guide.md",
                    "documentKind": "not-a-kind",
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            })

            with self.assertRaisesRegex(MapError, "unknown document kind"):
                load_map(root)

    def test_rejects_malformed_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_map(root, {
                "guide": {
                    "path": "docs/guide.md",
                    "documentKind": "topic",
                    "sections": {
                        "coverage": "Cosa copre questo documento",
                        "context": "Contesto",
                    },
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            })

            with self.assertRaisesRegex(MapError, "missing required sections"):
                load_map(root)

    def test_sections_require_a_document_kind(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_map(root, {
                "guide": {
                    "path": "docs/guide.md",
                    "sections": {"coverage": "Cosa copre"},
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            })

            with self.assertRaisesRegex(MapError, "requires documentKind"):
                load_map(root)

    def test_legacy_audit_only_patterns_key_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            map_path = self._write_map(root, {})
            data = json.loads(map_path.read_text(encoding="utf-8"))
            data["settings"]["auditOnlyPatterns"] = ["/tmp/audit/**"]
            map_path.write_text(json.dumps(data), encoding="utf-8")

            documentation_map = load_map(root)

            self.assertEqual([], documentation_map.validate())
            self.assertIn("auditOnlyPatterns", documentation_map.settings)

    def test_active_documents_exempt_metadata_archives_and_non_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs" / "_meta").mkdir(parents=True)
            (root / "docs" / "_archive").mkdir(parents=True)
            (root / "docs" / "_analysis").mkdir(parents=True)
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "docs" / "_meta" / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (root / "docs" / "_archive" / "old.md").write_text("# Old\n", encoding="utf-8")
            (root / "docs" / "_analysis" / "report.md").write_text("# Report\n", encoding="utf-8")
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
                        "documentKind": "topic",
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
                "documents": {"guide": {"path": "docs/guide.md", "documentKind": "topic"}},
            })
            (root / "docs").mkdir()
            (root / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")

            issues = documentation_issues(root, documentation_map)

            self.assertIn("Unregistered documentation index: docs/index.md", issues.index)
            self.assertNotIn("docs/index.md", issues.unregistered)

    def test_glob_semantics_apply_to_ignore_and_source_patterns(self):
        documentation_map = DocumentationMap(Path("map.json"), {
            "schemaVersion": 1,
            "settings": {"ignorePatterns": ["src/*.tmp"]},
            "documents": {
                "single": {
                    "path": "docs/single.md",
                    "documentKind": "topic",
                    "sourcePatterns": ["src/*.py"],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
                "recursive": {
                    "path": "docs/recursive.md",
                    "sourcePatterns": ["src/**"],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
                "tests": {
                    "path": "docs/tests.md",
                    "sourcePatterns": ["**/test/**"],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            },
        })

        self.assertTrue(documentation_map.is_ignored("src/a.tmp"))
        self.assertFalse(documentation_map.is_ignored("src/nested/a.tmp"))
        self.assertEqual({"single", "recursive"}, documentation_map.matching_documents("src/a.py"))
        self.assertEqual({"recursive"}, documentation_map.matching_documents("src/a/b.py"))
        self.assertEqual({"tests"}, documentation_map.matching_documents("test/a.py"))
        self.assertEqual({"recursive", "tests"}, documentation_map.matching_documents("src/test/a.py"))

    def test_legacy_map_keeps_fnmatch_semantics(self):
        documentation_map = DocumentationMap(Path("map.json"), {
            "schemaVersion": 1,
            "settings": {"ignorePatterns": ["src/*.tmp"]},
            "documents": {
                "single": {
                    "path": "docs/single.md",
                    "sourcePatterns": ["src/*.py"],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            },
        })

        self.assertFalse(documentation_map.is_canonical)
        self.assertTrue(documentation_map.is_ignored("src/nested/a.tmp"))
        self.assertEqual({"single"}, documentation_map.matching_documents("src/a/b.py"))

    def test_legacy_map_reports_document_issues_as_warnings_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            documentation_map = DocumentationMap(Path("map.json"), {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "guide": {"path": "docs/guide.md", "sourcePatterns": [], "sourceHashes": {}},
                },
            })
            (root / "docs").mkdir()
            (root / "docs" / "orphan.md").write_text("# Orphan\n", encoding="utf-8")

            issues = documentation_issues(root, documentation_map)

            self.assertEqual((), issues.errors)
            self.assertIn("Unregistered document: docs/orphan.md", issues.warnings)
            self.assertIn("Missing document: docs/guide.md", issues.warnings)

    def test_recognizes_new_infrastructure_mobile_and_frontend_sources(self):
        documentation_map = DocumentationMap(Path("map.json"), {
            "schemaVersion": 1,
            "settings": {},
            "documents": {},
        })

        for path in (
            "infra/main.tf",
            "infra/production.tfvars",
            "infra/config.hcl",
            "infra/main.bicep",
            "infra/flake.nix",
            "mobile/lib/main.dart",
            "mobile/ios/AppDelegate.m",
            "mobile/ios/View.mm",
            "firmware/sketch.ino",
            "web/App.vue",
            "web/App.svelte",
            "web/page.astro",
            "web/index.html",
            "web/styles.scss",
            "web/styles.less",
            "web/styles.sass",
            "web/styles.styl",
            "config/app.ini",
            "config/app.cfg",
            "config/app.conf",
        ):
            with self.subTest(path=path):
                self.assertTrue(documentation_map.is_relevant_source(path))

    def test_relevant_names_are_case_insensitive(self):
        documentation_map = DocumentationMap(Path("map.json"), {
            "schemaVersion": 1,
            "settings": {},
            "documents": {},
        })

        for path in (
            "Dockerfile",
            "dockerfile",
            "DOCKERFILE",
            "Containerfile",
            "Caddyfile",
            "Procfile",
            "nginx.conf",
            "kustomization.yaml",
            "Chart.yaml",
            "values.yaml",
        ):
            with self.subTest(path=path):
                self.assertTrue(documentation_map.is_relevant_source(path))

    def test_lockfiles_and_generated_outputs_are_not_relevant_sources(self):
        documentation_map = DocumentationMap(Path("map.json"), {
            "schemaVersion": 1,
            "settings": {},
            "documents": {},
        })

        for path in (
            "package-lock.json",
            "npm-shrinkwrap.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lockb",
            "Cargo.lock",
            "poetry.lock",
            "Pipfile.lock",
            "composer.lock",
            "Gemfile.lock",
            "go.sum",
            "flake.lock",
            "static/main.min.js",
            "static/main.min.css",
            "static/main.js.map",
            "lib/model.g.dart",
            "lib/model.freezed.dart",
            "proto/service.pb.go",
            "proto/service_pb2.py",
        ):
            with self.subTest(path=path):
                self.assertFalse(documentation_map.is_relevant_source(path))


if __name__ == "__main__":
    unittest.main()
