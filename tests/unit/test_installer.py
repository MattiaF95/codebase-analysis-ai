import io
import sys
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

import install as skill_distribution_installer  # noqa: E402
from codebase_analysis_ai import project_installer  # noqa: E402
from codebase_analysis_ai.project_installer import START, append_managed_block_if_missing, install_project_components  # noqa: E402


class InstallerTest(unittest.TestCase):
    def test_skill_update_preserves_extra_files_and_rejects_unmanaged_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            managed = root / "managed"
            skill_distribution_installer.install_skill(managed)
            extra = managed / "manual-note.md"
            extra.write_text("keep\n", encoding="utf-8")
            skill_file = managed / "SKILL.md"
            skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\noutdated\n", encoding="utf-8")

            skill_distribution_installer.install_skill(managed)

            self.assertEqual("keep\n", extra.read_text(encoding="utf-8"))
            self.assertEqual(
                (ROOT / "skill" / "codebase-analysis-ai" / "SKILL.md").read_text(encoding="utf-8"),
                (managed / "SKILL.md").read_text(encoding="utf-8"),
            )

            unmanaged = root / "unmanaged"
            unmanaged.mkdir()
            custom = unmanaged / "custom.txt"
            custom.write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unmanaged skill target"):
                skill_distribution_installer.install_skill(unmanaged)
            self.assertEqual("keep\n", custom.read_text(encoding="utf-8"))

    def test_managed_block_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            block = f"{START}\nRule one.\n<!-- codebase-analysis-ai:end -->"
            append_managed_block_if_missing(target, block)
            append_managed_block_if_missing(target, block)
            content = target.read_text(encoding="utf-8")
            self.assertEqual(1, content.count(START))
            self.assertIn("Keep this.", content)

    def test_existing_managed_automation_is_refreshed_and_missing_files_are_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            hook = root / ".githooks" / "post-commit"
            hook.parent.mkdir()
            hook.write_text("#!/bin/sh\n# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            hook.chmod(0o600)
            action = root / ".github" / "workflows" / "codebase-analysis-ai.yml"
            action.parent.mkdir(parents=True)
            action.write_text("# Managed by Codebase Analysis AI.\ncustom\n", encoding="utf-8")
            install_project_components(root, ["codex"], False, True, True)
            self.assertNotIn("custom", hook.read_text(encoding="utf-8"))
            self.assertNotEqual(0, hook.stat().st_mode & 0o111)
            self.assertNotIn("custom", action.read_text(encoding="utf-8"))
            self.assertIn("check --mode pre-push", (root / ".githooks" / "pre-push").read_text(encoding="utf-8"))

            second_changes = install_project_components(root, ["codex"], False, True, True)
            self.assertNotIn(".githooks/post-commit", second_changes)
            self.assertNotIn(".github/workflows/codebase-analysis-ai.yml", second_changes)

    def test_agent_file_is_append_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "AGENTS.md"
            target.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            install_project_components(root, ["codex"], True, False, False)
            first = target.read_text(encoding="utf-8")
            self.assertIn("Keep this.", first)
            install_project_components(root, ["codex"], True, False, False)
            self.assertEqual(first, target.read_text(encoding="utf-8"))

    def test_existing_managed_agent_block_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "AGENTS.md"
            target.write_text(
                "# Existing\n\n<!-- codebase-analysis-ai:start -->\nold rule\n"
                "<!-- codebase-analysis-ai:end -->\n\n# Manual\n",
                encoding="utf-8",
            )

            install_project_components(root, ["codex"], True, False, False)

            content = target.read_text(encoding="utf-8")
            self.assertIn("# Existing", content)
            self.assertIn("# Manual", content)
            self.assertIn("Hook interruption protocol", content)
            self.assertNotIn("old rule", content)

    def test_unmanaged_runtime_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "tools" / "codebase-analysis-ai"
            package = runtime / "codebase_analysis_ai"
            package.mkdir(parents=True)
            (runtime / "check.py").write_text("local runtime", encoding="utf-8")
            (package / "custom.py").write_text("local module", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "unmanaged runtime"):
                install_project_components(root, ["codex"], False, False, False)

            self.assertEqual("local module", (package / "custom.py").read_text(encoding="utf-8"))

    def test_existing_managed_runtime_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_components(root, ["codex"], False, False, False)
            runtime = root / "tools" / "codebase-analysis-ai"
            module = runtime / "codebase_analysis_ai" / "source_hashes.py"
            module.write_text("outdated\n", encoding="utf-8")

            changes = install_project_components(root, ["codex"], False, False, False)

            self.assertIn(
                "tools/codebase-analysis-ai/codebase_analysis_ai/source_hashes.py",
                changes,
            )
            self.assertNotEqual("outdated\n", module.read_text(encoding="utf-8"))

    def test_unexpected_runtime_python_files_are_reported_not_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_components(root, ["codex"], False, False, False)
            extra = root / "tools" / "codebase-analysis-ai" / "codebase_analysis_ai" / "obsolete" / "old.py"
            extra.parent.mkdir()
            extra.write_text("old\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "unexpected installed files"):
                install_project_components(root, ["codex"], False, False, False)

            self.assertEqual("old\n", extra.read_text(encoding="utf-8"))

    def test_existing_hooks_path_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "custom-hooks").mkdir()
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", "custom-hooks"], check=True)

            with self.assertRaisesRegex(RuntimeError, "core.hooksPath"):
                install_project_components(root, ["codex"], False, True, False)
            self.assertFalse((root / "tools" / "codebase-analysis-ai").exists())

    def test_missing_githooks_and_stale_hooks_path_are_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", "missing-hooks"], check=True)

            install_project_components(root, ["codex"], False, True, False)

            self.assertTrue((root / ".githooks" / "pre-push").is_file())
            self.assertEqual(".githooks", subprocess.run(
                ["git", "-C", str(root), "config", "--get", "core.hooksPath"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.strip())

    def test_current_managed_hook_permissions_are_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            install_project_components(root, ["codex"], False, True, False)
            hook = root / ".githooks" / "pre-push"
            hook.chmod(0o600)

            changes = install_project_components(root, ["codex"], False, True, False)

            self.assertNotEqual(0, hook.stat().st_mode & 0o111)
            self.assertIn(".githooks/pre-push", changes)

    def test_conflicting_targets_stop_before_runtime_is_created(self):
        cases = {
            "unmanaged hook": (".githooks/pre-push", "#!/bin/sh\ncustom\n", ["codex"], False, True, False),
            "unmanaged workflow": (
                ".github/workflows/codebase-analysis-ai.yml",
                "name: custom\n",
                ["codex"],
                False,
                False,
                True,
            ),
            "incomplete agent block": (
                "AGENTS.md",
                f"{START}\nincomplete\n",
                ["codex"],
                True,
                False,
                False,
            ),
        }
        for label, (relative, content, agents, with_agents, with_hooks, with_action) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

                with self.assertRaises(RuntimeError):
                    install_project_components(root, agents, with_agents, with_hooks, with_action)

                self.assertFalse((root / "tools" / "codebase-analysis-ai").exists())

    def test_runtime_extra_non_python_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install_project_components(root, ["codex"], False, False, False)
            runtime = root / "tools" / "codebase-analysis-ai"
            note = runtime / "codebase_analysis_ai" / "notes.txt"
            note.write_text("local note\n", encoding="utf-8")
            root_note = runtime / "extra.json"
            root_note.write_text("{}\n", encoding="utf-8")

            install_project_components(root, ["codex"], False, False, False)

            self.assertEqual("local note\n", note.read_text(encoding="utf-8"))
            self.assertEqual("{}\n", root_note.read_text(encoding="utf-8"))

    def test_external_githooks_symlink_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "hooks"
            external.mkdir()
            (root / ".githooks").symlink_to(external, target_is_directory=True)

            with self.assertRaisesRegex(project_installer.InstallConflict, "symlink outside project"):
                install_project_components(root, ["codex"], False, True, False)

            self.assertEqual([], list(external.iterdir()))
            self.assertFalse((root / "tools").exists())

    def test_external_tools_symlink_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "tools"
            external.mkdir()
            (root / "tools").symlink_to(external, target_is_directory=True)

            with self.assertRaisesRegex(project_installer.InstallConflict, "symlink outside project"):
                install_project_components(root, ["codex"], False, False, False)

            self.assertEqual([], list(external.iterdir()))

    def test_external_github_symlink_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "github"
            external.mkdir()
            (root / ".github").symlink_to(external, target_is_directory=True)

            with self.assertRaisesRegex(project_installer.InstallConflict, "symlink outside project"):
                install_project_components(root, ["codex"], False, False, True)

            self.assertEqual([], list(external.iterdir()))
            self.assertFalse((root / "tools").exists())

    def test_failure_after_skill_install_restores_new_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            argv = ["install.py", "--project-root", str(root), "--agent", "codex"]
            stderr = io.StringIO()

            with mock.patch.object(
                skill_distribution_installer,
                "install_project_components",
                side_effect=OSError("injected project failure"),
            ), mock.patch.object(sys, "argv", argv), redirect_stderr(stderr):
                result = skill_distribution_installer.main()

            self.assertEqual(2, result)
            self.assertIn("Codebase Analysis AI setup stopped", stderr.getvalue())
            self.assertIn("injected project failure", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertFalse((root / ".agents").exists())

    def test_failure_after_skill_install_restores_previous_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            target = skill_distribution_installer.destination("codex", "project", root)
            skill_distribution_installer.install_skill(target)
            skill_file = target / "SKILL.md"
            previous = skill_file.read_text(encoding="utf-8") + "\nlocal change\n"
            skill_file.write_text(previous, encoding="utf-8")
            skill_file.chmod(0o600)
            extra = target / "keep.txt"
            extra.write_text("keep\n", encoding="utf-8")
            argv = ["install.py", "--project-root", str(root), "--agent", "codex"]
            stderr = io.StringIO()

            with mock.patch.object(
                skill_distribution_installer,
                "install_project_components",
                side_effect=RuntimeError("injected project failure"),
            ), mock.patch.object(sys, "argv", argv), redirect_stderr(stderr):
                result = skill_distribution_installer.main()

            self.assertEqual(2, result)
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertEqual(previous, skill_file.read_text(encoding="utf-8"))
            self.assertEqual(0o600, skill_file.stat().st_mode & 0o777)
            self.assertEqual("keep\n", extra.read_text(encoding="utf-8"))

    def test_preflight_conflict_stops_before_skill_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".githooks").mkdir()
            (root / ".githooks" / "pre-push").write_text("#!/bin/sh\ncustom\n", encoding="utf-8")
            argv = ["install.py", "--project-root", str(root), "--agent", "codex"]
            stderr = io.StringIO()

            with mock.patch.object(sys, "argv", argv), redirect_stderr(stderr):
                result = skill_distribution_installer.main()

            self.assertEqual(2, result)
            self.assertIn("Codebase Analysis AI setup stopped", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertFalse((root / ".agents").exists())

    def test_failure_rolls_back_files_permissions_and_git_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", "missing-hooks"], check=True)
            agents = root / "AGENTS.md"
            agents.write_text("# Manual rules\n", encoding="utf-8")
            original_copy = project_installer._copy_managed_file

            def fail_on_workflow(source, target, replacements=None):
                if target.name == "codebase-analysis-ai.yml":
                    raise OSError("injected write failure")
                return original_copy(source, target, replacements)

            with mock.patch.object(project_installer, "_copy_managed_file", side_effect=fail_on_workflow):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    install_project_components(root, ["codex"], True, True, True)

            self.assertEqual("# Manual rules\n", agents.read_text(encoding="utf-8"))
            self.assertFalse((root / "tools").exists())
            self.assertFalse((root / ".githooks").exists())
            self.assertFalse((root / ".github").exists())
            configured = subprocess.run(
                ["git", "-C", str(root), "config", "--local", "--get", "core.hooksPath"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.strip()
            self.assertEqual("missing-hooks", configured)


if __name__ == "__main__":
    unittest.main()
