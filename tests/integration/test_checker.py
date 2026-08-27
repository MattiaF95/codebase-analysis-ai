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

    def test_accepts_manual_document_change_without_validating_or_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            run("git", "init", "-b", "main", cwd=project)
            run("git", "config", "user.name", "Test", cwd=project)
            run("git", "config", "user.email", "test@example.com", cwd=project)
            docs = project / "docs"
            (docs / "_meta").mkdir(parents=True)
            document = docs / "guide.md"
            document.write_text("# Guide\n\n[Manual link](missing.md)\n", encoding="utf-8")
            (docs / "_meta" / "documentation-map.json").write_text(json.dumps({
                "schemaVersion": 1,
                "settings": {},
                "documents": {
                    "guide": {
                        "path": "docs/guide.md",
                        "sourcePatterns": [],
                        "sourceHashes": {},
                        "relatedDocuments": [],
                    }
                },
            }), encoding="utf-8")
            run("git", "add", ".", cwd=project)
            run("git", "commit", "-qm", "Initial", cwd=project)

            document.write_text("# Manually updated guide\n\n[Broken manual link](missing.md)\n", encoding="utf-8")
            result = run(
                sys.executable, str(CLI), "--root", str(project), "check", "--mode", "working-tree", "--json", cwd=project
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(["docs/guide.md"], report["changedDocuments"])
            self.assertEqual([], report["linkErrors"])
            self.assertEqual("# Manually updated guide\n\n[Broken manual link](missing.md)\n", document.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
