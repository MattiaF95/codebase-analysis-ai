import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.git_changes import ZERO_SHA, paths, pre_push_changes  # noqa: E402


class GitChangesTest(unittest.TestCase):
    def test_new_branch_push_includes_every_unpublished_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)

            (root / "one.py").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "one.py"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "one"], check=True)
            (root / "two.py").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "two.py"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "two"], check=True)
            head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            changes = pre_push_changes(
                root,
                [f"refs/heads/example {head} refs/heads/example {ZERO_SHA}\n"],
            )

            self.assertEqual(["one.py", "two.py"], paths(changes))


if __name__ == "__main__":
    unittest.main()
