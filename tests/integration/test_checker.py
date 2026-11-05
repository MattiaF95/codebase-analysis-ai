import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "skill" / "codebase-analysis-ai" / "scripts" / "codebase_analysis_ai.py"


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


class CheckerIntegrationTest(unittest.TestCase):
    def test_malformed_ci_event_returns_clean_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "_meta" / "documentation-map.json").write_text(
                json.dumps({"schemaVersion": 1, "settings": {}, "documents": {}}),
                encoding="utf-8",
            )
            event = project / "event.json"
            event.write_text("{invalid", encoding="utf-8")

            result = run(
                sys.executable,
                str(CLI),
                "--root",
                str(project),
                "check",
                "--mode",
                "ci",
                "--event-name",
                "pull_request",
                "--event-path",
                str(event),
                cwd=project,
            )

            self.assertEqual(2, result.returncode)
            self.assertIn("invalid CI event payload", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_malformed_map_returns_clean_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "_meta" / "documentation-map.json").write_text(
                json.dumps({"schemaVersion": 1, "settings": [], "documents": ["invalid"]}),
                encoding="utf-8",
            )

            result = run(
                sys.executable,
                str(CLI),
                "--root",
                str(project),
                "check",
                "--mode",
                "working-tree",
                cwd=project,
            )

            self.assertEqual(2, result.returncode)
            self.assertIn("Invalid documentation map", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_detects_and_refreshes_stale_source(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            (project / "src").mkdir()
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (project / "docs" / "backend.md").write_text(
                "# Backend\n\n## Related documentation\n\nNo direct links.\n", encoding="utf-8"
            )
            source = project / "src" / "Service.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            mapping = {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "backend": {
                        "path": "docs/backend.md",
                        "sourcePatterns": ["src/**"],
                        "sourceHashes": {"src/Service.py": digest},
                        "relatedDocuments": [],
                    }
                },
            }
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps(mapping), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-m", "Initial", cwd=project)

            source.write_text("VALUE = 2\n", encoding="utf-8")
            failed = run(sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", cwd=project)
            self.assertEqual(1, failed.returncode, failed.stdout + failed.stderr)
            self.assertIn("Stale", failed.stderr)

            refreshed = run(sys.executable, str(CLI), "--root", str(project), "refresh", "src/Service.py", cwd=project)
            self.assertEqual(0, refreshed.returncode, refreshed.stdout + refreshed.stderr)
            passed = run(sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", cwd=project)
            self.assertEqual(0, passed.returncode, passed.stdout + passed.stderr)

    def test_validates_links_in_manual_document_change_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            document = docs / "guide.md"
            document.write_text("# Guide\n\n[Manual link](missing.md)\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "guide": {
                        "path": "docs/guide.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            document.write_text("# Manually updated guide\n\n[Broken manual link](missing.md)\n", encoding="utf-8")
            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["docs/guide.md"], report["changedDocuments"])
            self.assertTrue(report["linkErrors"])
            self.assertIn("docs/guide.md: broken link: missing.md", report["linkErrors"])
            self.assertEqual("# Manually updated guide\n\n[Broken manual link](missing.md)\n", document.read_text(encoding="utf-8"))


    def test_reports_missing_registered_document(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                    "guide": {"path": "docs/guide.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            (docs / "guide.md").unlink()
            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["docs/guide.md"], report["missingDocuments"])
            self.assertIn("Missing document: docs/guide.md", report["errors"])

    def test_reports_deleted_documentation_index(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                    "guide": {"path": "docs/guide.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            (docs / "index.md").unlink()
            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("Missing documentation index: docs/index.md", report["indexErrors"])
            self.assertEqual(["docs/index.md"], report["missingDocuments"])

    def test_reports_unregistered_documentation_index(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "guide": {"path": "docs/guide.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("Unregistered documentation index: docs/index.md", report["indexErrors"])

    def test_reports_unregistered_active_documents_but_exempts_metadata_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "_archive").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (docs / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            (docs / "_meta" / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (docs / "_archive" / "old.md").write_text("# Old\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["docs/orphan.md"], report["unregisteredDocuments"])
            self.assertEqual([], report["missingDocuments"])
            self.assertIn("Unregistered document: docs/orphan.md", report["errors"])

    def test_deleted_mapped_source_is_not_unmapped_but_requires_map_maintenance(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            source = project / "src" / "old.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {"src/old.py": digest},
                        "relatedDocuments": [],
                    },
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            source.unlink()
            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual([], report["unmappedFiles"])
            self.assertEqual(["src/old.py -> index"], report["removedMappings"])
            self.assertIn("Removed source still mapped: src/old.py -> index", report["errors"])

    def test_rename_reports_old_mapping_without_unmapped_old_path_and_checks_new_path(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            (docs / "index.md").write_text("# Documentation\n", encoding="utf-8")
            source = project / "src" / "old.py"
            source.parent.mkdir()
            source.write_text("VALUE = 1\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": ["src/**"],
                        "sourceHashes": {"src/old.py": digest},
                        "relatedDocuments": [],
                    },
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)
            run("git", "mv", "src/old.py", "src/new.py", cwd=project)

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertNotIn("src/old.py", report["unmappedFiles"])
            self.assertNotIn("src/new.py", report["unmappedFiles"])
            self.assertEqual(["index"], report["directDocuments"])
            self.assertEqual(["src/old.py -> index"], report["removedMappings"])

    def test_document_coverage_failure_honors_warn_only(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (project / "docs" / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")

            strict = run(
                sys.executable, str(CLI), "--root", str(project),
                "check", "--mode", "working-tree", "--json", cwd=project,
            )
            warned = run(
                sys.executable, str(CLI), "--root", str(project),
                "check", "--mode", "working-tree", "--warn-only", "--json", cwd=project,
            )

            self.assertEqual(1, strict.returncode, strict.stdout + strict.stderr)
            self.assertEqual(0, warned.returncode, warned.stdout + warned.stderr)
            self.assertTrue(json.loads(warned.stdout)["errors"])

    def test_invalid_ignore_pattern_honors_warn_only_and_emits_json(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {"ignorePatterns": ["../outside/**"]},
                "documents": {},
            }), encoding="utf-8")

            warned = run(
                sys.executable, str(CLI), "--root", str(project),
                "check", "--mode", "working-tree", "--warn-only", "--json", cwd=project,
            )
            strict = run(
                sys.executable, str(CLI), "--root", str(project),
                "check", "--mode", "working-tree", "--json", cwd=project,
            )

            self.assertEqual(0, warned.returncode, warned.stdout + warned.stderr)
            self.assertEqual(2, strict.returncode, strict.stdout + strict.stderr)
            self.assertNotIn("Traceback", warned.stderr)
            self.assertNotIn("Traceback", strict.stderr)
            warned_report = json.loads(warned.stdout)
            strict_report = json.loads(strict.stdout)
            self.assertTrue(warned_report["mapErrors"])
            self.assertTrue(strict_report["mapErrors"])

    def test_git_failure_honors_warn_only_and_emits_json(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "_meta").mkdir(parents=True)
            (project / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                },
            }), encoding="utf-8")
            event = project / "event.json"
            event.write_text("{invalid", encoding="utf-8")

            warned = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "ci",
                "--event-name", "pull_request", "--event-path", str(event), "--warn-only", "--json", cwd=project,
            )
            strict = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "ci",
                "--event-name", "pull_request", "--event-path", str(event), "--json", cwd=project,
            )

            self.assertEqual(0, warned.returncode, warned.stdout + warned.stderr)
            self.assertEqual(2, strict.returncode, strict.stdout + strict.stderr)
            self.assertNotIn("Traceback", warned.stderr)
            self.assertNotIn("Traceback", strict.stderr)
            self.assertTrue(json.loads(warned.stdout)["errors"])
            self.assertTrue(json.loads(strict.stdout)["errors"])

    def test_check_reports_navigation_and_missing_coverage_for_declared_index(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "backend").mkdir(parents=True)
            (project / "docs" / "_meta").mkdir()
            (project / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (project / "docs" / "backend" / "index.md").write_text("# Backend\n", encoding="utf-8")
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "documentKind": "documentation-index",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "backend": {
                        "path": "docs/backend/index.md",
                        "documentKind": "area",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            }), encoding="utf-8")

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json",
                cwd=project,
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(any("docs/backend/index.md" in error for error in report["navigationErrors"]))
            self.assertTrue(any("Missing documentation coverage" in error for error in report["coverageErrors"]))

    def test_check_reports_invalid_adr_and_honors_warn_only(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "decisions").mkdir(parents=True)
            (project / "docs" / "_meta").mkdir()
            (project / "docs" / "index.md").write_text(
                "# Documentation\n\n[Decisions](decisions/index.md)\n", encoding="utf-8"
            )
            (project / "docs" / "decisions" / "index.md").write_text(
                "# Decision records\n\n## What this index covers\n\nIndice.\n\n"
                "## Accepted\n\n- [ADR](ADR-0001-auth.md)\n\n"
                "## Related documentation\n\nNessun collegamento.\n",
                encoding="utf-8",
            )
            (project / "docs" / "decisions" / "ADR-0001-auth.md").write_text(
                "# ADR-0001: Authentication\n\n"
                "<!-- codebase-analysis-ai:scope:start -->\nRationale.\n"
                "<!-- codebase-analysis-ai:scope:end -->\n\n"
                "## Context\n\nContesto.\n\n## Decision\n\nDecisione.\n\n"
                "## Alternatives considered\n\nAlternative.\n\n"
                "## Consequences\n\nConseguenze.\n\n## Evidence\n\nEvidenza.\n\n"
                "## Links\n\nCollegamenti.\n",
                encoding="utf-8",
            )
            sections = {
                "context": "Context",
                "decision": "Decision",
                "alternatives": "Alternatives considered",
                "consequences": "Consequences",
                "evidence": "Evidence",
                "links": "Links",
            }
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "decisions": {
                        "path": "docs/decisions/index.md",
                        "documentKind": "kind-index",
                        "sections": {
                            "coverage": "What this index covers",
                            "relatedDocumentation": "Related documentation",
                        },
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "adr": {
                        "path": "docs/decisions/ADR-0001-auth.md",
                        "documentKind": "decision-record",
                        "sections": sections,
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                        "metadata": {"status": "superseded", "date": "2026-01-31"},
                    },
                },
            }), encoding="utf-8")

            strict = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json",
                cwd=project,
            )
            warned = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree",
                "--warn-only", "--json", cwd=project,
            )

            self.assertEqual(1, strict.returncode, strict.stdout + strict.stderr)
            strict_report = json.loads(strict.stdout)
            self.assertTrue(any("supersededBy" in error for error in strict_report["adrErrors"]))
            self.assertEqual(0, warned.returncode, warned.stdout + warned.stderr)
            self.assertTrue(json.loads(warned.stdout)["adrErrors"])

    def test_status_only_adr_change_does_not_produce_stale_document_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            (project / "docs" / "decisions").mkdir(parents=True)
            (project / "docs" / "_meta").mkdir()
            (project / "docs" / "index.md").write_text(
                "# Documentation\n\n[Decisions](decisions/index.md)\n", encoding="utf-8"
            )
            (project / "docs" / "decisions" / "index.md").write_text(
                "# Decision records\n\n## What this index covers\n\nIndice.\n\n"
                "## Proposed\n\n- [ADR](ADR-0001-auth.md)\n\n"
                "## Related documentation\n\nNessun collegamento.\n",
                encoding="utf-8",
            )
            (project / "docs" / "decisions" / "ADR-0001-auth.md").write_text(
                "# ADR-0001: Authentication\n\n"
                "<!-- codebase-analysis-ai:scope:start -->\nRationale.\n"
                "<!-- codebase-analysis-ai:scope:end -->\n\n"
                "## Context\n\nContesto.\n\n## Decision\n\nDecisione.\n\n"
                "## Alternatives considered\n\nAlternative.\n\n"
                "## Consequences\n\nConseguenze.\n\n## Evidence\n\nEvidenza.\n\n"
                "## Links\n\nCollegamenti.\n",
                encoding="utf-8",
            )
            sections = {
                "context": "Context",
                "decision": "Decision",
                "alternatives": "Alternatives considered",
                "consequences": "Consequences",
                "evidence": "Evidence",
                "links": "Links",
            }
            mapping = {
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {"path": "docs/index.md", "sourcePatterns": [], "sourceHashes": {}, "relatedDocuments": []},
                    "decisions": {
                        "path": "docs/decisions/index.md",
                        "documentKind": "kind-index",
                        "sections": {
                            "coverage": "What this index covers",
                            "relatedDocumentation": "Related documentation",
                        },
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "adr": {
                        "path": "docs/decisions/ADR-0001-auth.md",
                        "documentKind": "decision-record",
                        "sections": sections,
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                        "metadata": {"status": "proposed", "date": "2026-01-31"},
                    },
                },
            }
            map_path = project / "docs" / "_meta" / "documentation-map.json"
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            mapping["documents"]["adr"]["metadata"]["status"] = "accepted"
            map_path.write_text(json.dumps(mapping), encoding="utf-8")

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json",
                cwd=project,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual([], json.loads(result.stdout)["staleMappings"])

    def test_check_keeps_legacy_index_navigation_non_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            (project / "docs" / "backend").mkdir(parents=True)
            (project / "docs" / "_meta").mkdir()
            (project / "docs" / "index.md").write_text("# Documentation\n", encoding="utf-8")
            (project / "docs" / "backend" / "index.md").write_text("# Backend\n", encoding="utf-8")
            (project / "docs" / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "index": {
                        "path": "docs/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                    "backend": {
                        "path": "docs/backend/index.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    },
                },
            }), encoding="utf-8")

            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json",
                cwd=project,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual([], report["navigationErrors"])
            self.assertEqual([], report["coverageErrors"])


if __name__ == "__main__":
    unittest.main()
