import subprocess
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.git_changes import (  # noqa: E402
    Change,
    GitError,
    ZERO_SHA,
    ci_event_changes,
    new_ref_changes,
    paths,
    pre_push_changes,
    rewrite_changes,
    working_tree_changes,
)


class GitChangesTest(unittest.TestCase):
    @staticmethod
    def _repository(directory: str) -> Path:
        root = Path(directory)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
        return root

    @staticmethod
    def _commit(root: Path, path: str, content: str, message: str) -> str:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", path], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", message], check=True)
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def test_rename_exposes_old_and_new_paths_but_copy_exposes_only_destination(self):
        changes = [
            Change(path="src/new.py", old_path="src/old.py", status="R"),
            Change(path="src/copy.py", old_path="src/new.py", status="C"),
        ]

        self.assertEqual(
            ["src/old.py", "src/new.py", "src/copy.py"],
            paths(changes),
        )

    def test_new_branch_push_includes_every_unpublished_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            self._commit(root, "one.py", "one\n", "one")
            head = self._commit(root, "two.py", "two\n", "two")

            changes = pre_push_changes(
                root,
                [f"refs/heads/example {head} refs/heads/example {ZERO_SHA}\n"],
            )

            self.assertEqual(["one.py", "two.py"], paths(changes))

    def test_existing_branch_push_and_rewrite_use_complete_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            base = self._commit(root, "one.py", "one\n", "base")
            head = self._commit(root, "two.py", "two\n", "head")

            pushed = pre_push_changes(
                root,
                [f"refs/heads/main {head} refs/heads/main {base}\n"],
            )
            rewritten = rewrite_changes(root, [f"{base} {head}\n"])

            self.assertEqual(["two.py"], paths(pushed))
            self.assertEqual(["two.py"], paths(rewritten))

    def test_ci_new_branch_push_includes_all_unpublished_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            self._commit(root, "one.py", "one\n", "one")
            head = self._commit(root, "two.py", "two\n", "two")
            event = root / "event.json"
            event.write_text(json.dumps({"before": ZERO_SHA, "after": head}), encoding="utf-8")

            changes = ci_event_changes(root, "push", event)

            self.assertEqual(["one.py", "two.py"], paths(changes))

    def test_malformed_hook_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            self._commit(root, "base.py", "base\n", "base")

            with self.assertRaisesRegex(GitError, "invalid pre-push input"):
                pre_push_changes(root, ["malformed\n"])
            with self.assertRaisesRegex(GitError, "invalid post-rewrite input"):
                rewrite_changes(root, ["malformed\n"])

    def test_working_tree_preserves_tabs_newlines_and_unicode_in_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            self._commit(root, "base.py", "base\n", "base")
            special = "unicode-è\tline\n.py"
            (root / special).write_text("value\n", encoding="utf-8")

            self.assertIn(special, paths(working_tree_changes(root)))

    def test_new_ref_rejects_incomplete_shallow_history(self):
        with tempfile.TemporaryDirectory() as source_directory, tempfile.TemporaryDirectory() as clone_parent:
            source = self._repository(source_directory)
            self._commit(source, "one.py", "one\n", "one")
            self._commit(source, "two.py", "two\n", "two")
            clone = Path(clone_parent) / "clone"
            subprocess.run(
                ["git", "clone", "-q", "--depth", "1", source.as_uri(), str(clone)],
                check=True,
            )

            with self.assertRaisesRegex(GitError, "shallow history"):
                new_ref_changes(clone, "HEAD")

    def test_manual_dispatch_supports_root_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._repository(directory)
            self._commit(root, "root.py", "root\n", "root")
            event = root / "event.json"
            event.write_text("{}", encoding="utf-8")

            self.assertEqual(["root.py"], paths(ci_event_changes(root, "workflow_dispatch", event)))


if __name__ == "__main__":
    unittest.main()
