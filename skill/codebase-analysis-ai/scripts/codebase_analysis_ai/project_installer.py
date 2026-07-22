"""Install managed Codebase Analysis AI components into a target repository."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


START = "<!-- codebase-analysis-ai:start -->"
END = "<!-- codebase-analysis-ai:end -->"
MANAGED = "Managed by Codebase Analysis AI"
RUNTIME_MARKER = "Codebase Analysis AI deterministic CLI."


class InstallConflict(RuntimeError):
    pass


def skill_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _source_runtime_files(source_package: Path) -> set[Path]:
    return {
        source.relative_to(source_package)
        for source in source_package.rglob("*")
        if source.is_file() and source.suffix == ".py" and "__pycache__" not in source.parts
    }


def _unexpected_installed_runtime_files(project_root: Path) -> list[str]:
    source_package = skill_root() / "scripts" / "codebase_analysis_ai"
    installed_package = project_root / "tools" / "codebase-analysis-ai" / "codebase_analysis_ai"
    if not installed_package.is_dir():
        return []
    expected = _source_runtime_files(source_package)
    unexpected = []
    for installed in installed_package.rglob("*.py"):
        if "__pycache__" in installed.parts:
            continue
        relative = installed.relative_to(installed_package)
        if relative not in expected:
            unexpected.append(
                f"tools/codebase-analysis-ai/codebase_analysis_ai/{relative.as_posix()}"
            )
    return sorted(unexpected)


def _atomic_write(target: Path, content: bytes, mode: int | None = None) -> None:
    """Replace one file atomically without exposing partially written content."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_write_text(target: Path, content: str) -> None:
    current_mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    _atomic_write(target, content.encode("utf-8"), current_mode)


def _atomic_copy(source: Path, target: Path) -> None:
    _atomic_write(target, source.read_bytes(), stat.S_IMODE(source.stat().st_mode))


def update_managed_block(target: Path, block: str) -> str:
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if START in existing and END in existing:
        before, remainder = existing.split(START, 1)
        _old, after = remainder.split(END, 1)
        updated = before.rstrip() + "\n\n" + block.strip() + "\n" + after.lstrip("\n")
        action = "updated"
    else:
        separator = "\n\n" if existing.strip() else ""
        updated = existing.rstrip() + separator + block.strip() + "\n"
        action = "created" if not existing else "updated"
    _atomic_write_text(target, updated)
    return action


def append_managed_block_if_missing(target: Path, block: str) -> str | None:
    """Create or refresh the managed agent block without touching manual text."""
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if START in existing and END in existing:
        before, remainder = existing.split(START, 1)
        _old, after = remainder.split(END, 1)
        updated = before.rstrip() + "\n\n" + block.strip() + "\n" + after.lstrip("\n")
        if updated == existing:
            return None
        _atomic_write_text(target, updated)
        return "updated"
    if START in existing:
        raise InstallConflict(f"Refusing to modify incomplete managed block: {target}")
    separator = "\n\n" if existing.strip() else ""
    _atomic_write_text(target, existing.rstrip() + separator + block.strip() + "\n")
    return "created" if not existing else "updated"


def _copy_managed_file(source: Path, target: Path, replacements: dict[str, str] | None = None) -> str | None:
    content = source.read_text(encoding="utf-8")
    for old, new in (replacements or {}).items():
        content = content.replace(old, new)
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if MANAGED not in existing:
            raise InstallConflict(f"Refusing to overwrite unmanaged file: {target}")
        if existing == content:
            return None
        action = "updated"
    else:
        action = "created"
    _atomic_write_text(target, content)
    return action


def _preflight_runtime(project_root: Path) -> None:
    check = project_root / "tools" / "codebase-analysis-ai" / "check.py"
    if check.exists() and (
        not check.is_file()
        or RUNTIME_MARKER not in check.read_text(encoding="utf-8", errors="replace")
    ):
        raise InstallConflict(f"Refusing to overwrite unmanaged runtime: {check}")
    unexpected = _unexpected_installed_runtime_files(project_root)
    if unexpected:
        raise InstallConflict(
            "Refusing to refresh runtime with unexpected installed files: "
            + ", ".join(unexpected)
        )


def _preflight_agent_file(target: Path) -> None:
    if not target.exists():
        return
    if not target.is_file():
        raise InstallConflict(f"Refusing to modify non-file agent target: {target}")
    content = target.read_text(encoding="utf-8", errors="replace")
    if (START in content) != (END in content):
        raise InstallConflict(f"Refusing to modify incomplete managed block: {target}")


def _preflight_managed_file(target: Path) -> None:
    if not target.exists():
        return
    if not target.is_file():
        raise InstallConflict(f"Refusing to overwrite non-file target: {target}")
    if MANAGED not in target.read_text(encoding="utf-8", errors="replace"):
        raise InstallConflict(f"Refusing to overwrite unmanaged file: {target}")


def _copy_runtime(project_root: Path) -> list[str]:
    source_scripts = skill_root() / "scripts"
    destination = project_root / "tools" / "codebase-analysis-ai"
    destination.mkdir(parents=True, exist_ok=True)
    changes: list[str] = []
    check = destination / "check.py"
    if check.exists() and RUNTIME_MARKER not in check.read_text(encoding="utf-8", errors="replace"):
        raise InstallConflict(f"Refusing to overwrite unmanaged runtime: {check}")
    source_check = source_scripts / "codebase_analysis_ai.py"
    if not check.exists() or check.read_bytes() != source_check.read_bytes():
        _atomic_copy(source_check, check)
        changes.append("tools/codebase-analysis-ai/check.py")
    package_destination = destination / "codebase_analysis_ai"
    package_destination.mkdir(parents=True, exist_ok=True)
    for source in (source_scripts / "codebase_analysis_ai").rglob("*"):
        if not source.is_file() or source.suffix in {".pyc"} or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(source_scripts / "codebase_analysis_ai")
        target = package_destination / relative
        if not target.exists() or target.read_bytes() != source.read_bytes():
            _atomic_copy(source, target)
            changes.append(f"tools/codebase-analysis-ai/codebase_analysis_ai/{relative.as_posix()}")
    return changes


def _detect_default_branch(project_root: Path) -> str:
    commands = [
        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        ["git", "branch", "--show-current"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        value = result.stdout.strip()
        if value:
            return value.removeprefix("origin/")
    return "main"


def _mutation_targets(
    project_root: Path,
    requested_agents: list[str],
    with_agent_rules: bool,
    with_hooks: bool,
    with_github_action: bool,
    agent_targets: dict[str, tuple[str, str]],
) -> list[Path]:
    source_scripts = skill_root() / "scripts"
    targets = [project_root / "tools" / "codebase-analysis-ai" / "check.py"]
    targets.extend(
        project_root / "tools" / "codebase-analysis-ai" / "codebase_analysis_ai" / source.relative_to(source_scripts / "codebase_analysis_ai")
        for source in (source_scripts / "codebase_analysis_ai").rglob("*")
        if source.is_file() and source.suffix != ".pyc" and "__pycache__" not in source.parts
    )
    if with_agent_rules:
        targets.extend(project_root / agent_targets[agent][1] for agent in requested_agents)
    if with_hooks:
        targets.extend(project_root / ".githooks" / name for name in ("post-commit", "pre-push", "post-merge", "post-rewrite"))
    if with_github_action:
        targets.append(project_root / ".github" / "workflows" / "codebase-analysis-ai.yml")
    return list(dict.fromkeys(targets))


def _snapshot_files(targets: Iterable[Path]) -> dict[Path, tuple[bytes, int] | None]:
    snapshot: dict[Path, tuple[bytes, int] | None] = {}
    for target in targets:
        snapshot[target] = (target.read_bytes(), stat.S_IMODE(target.stat().st_mode)) if target.is_file() else None
    return snapshot


def _missing_parent_directories(targets: Iterable[Path], project_root: Path) -> list[Path]:
    missing: set[Path] = set()
    for target in targets:
        parent = target.parent
        while parent != project_root and project_root in parent.parents:
            if not parent.exists():
                missing.add(parent)
            parent = parent.parent
    return sorted(missing, key=lambda path: len(path.parts), reverse=True)


def _restore_files(snapshot: dict[Path, tuple[bytes, int] | None]) -> None:
    for target, previous in snapshot.items():
        if previous is None:
            if target.is_file() or target.is_symlink():
                target.unlink()
            continue
        content, mode = previous
        _atomic_write(target, content, mode)


def _remove_created_directories(directories: Iterable[Path]) -> None:
    for directory in directories:
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            # Keep a directory when another process or manual action populated it.
            continue


def _local_hooks_path(project_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "config", "--local", "--get", "core.hooksPath"],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise InstallConflict(result.stderr.strip() or "Could not inspect local core.hooksPath")
    return result.stdout.strip() if result.returncode == 0 else None


def _restore_hooks_path(project_root: Path, previous: str | None) -> None:
    command = ["git", "config", "--local"]
    command.extend(["core.hooksPath", previous] if previous is not None else ["--unset-all", "core.hooksPath"])
    result = subprocess.run(command, cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode not in (0, 5):
        raise InstallConflict(result.stderr.strip() or "Could not restore core.hooksPath")


def install_project_components(
    project_root: Path,
    agents: Iterable[str],
    with_agent_rules: bool,
    with_hooks: bool,
    with_github_action: bool,
) -> list[str]:
    project_root = project_root.resolve()
    assets = skill_root() / "assets"
    agent_targets = {
        "codex": ("AGENTS.md", "AGENTS.md"),
        "claude": ("CLAUDE.md", "CLAUDE.md"),
        "gemini": ("GEMINI.md", "GEMINI.md"),
        "copilot": ("copilot-instructions.md", ".github/copilot-instructions.md"),
    }
    requested_agents = list(dict.fromkeys(agents))
    unknown_agents = [agent for agent in requested_agents if agent not in agent_targets]
    if unknown_agents:
        raise InstallConflict(f"Unknown agent targets: {', '.join(unknown_agents)}")

    hooks_path = ""
    if with_hooks and (project_root / ".git").exists():
        configured = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        hooks_path = configured.stdout.strip()
        if configured.returncode not in (0, 1):
            raise InstallConflict(configured.stderr.strip() or "Could not inspect core.hooksPath")
        if hooks_path and hooks_path != ".githooks":
            configured_path = Path(hooks_path)
            if not configured_path.is_absolute():
                configured_path = project_root / configured_path
            if configured_path.exists():
                raise InstallConflict(f"Refusing to replace existing core.hooksPath: {hooks_path}")
            # A stale path must not prevent setup. The installer will create
            # .githooks and replace the unusable local configuration below.
            hooks_path = ""

    _preflight_runtime(project_root)
    if with_agent_rules:
        for agent in requested_agents:
            _template_name, target_name = agent_targets[agent]
            _preflight_agent_file(project_root / target_name)
    if with_hooks:
        for hook_name in ("post-commit", "pre-push", "post-merge", "post-rewrite"):
            _preflight_managed_file(project_root / ".githooks" / hook_name)
    if with_github_action:
        _preflight_managed_file(project_root / ".github" / "workflows" / "codebase-analysis-ai.yml")

    mutation_targets = _mutation_targets(
        project_root,
        requested_agents,
        with_agent_rules,
        with_hooks,
        with_github_action,
        agent_targets,
    )
    snapshot = _snapshot_files(mutation_targets)
    created_directories = _missing_parent_directories(mutation_targets, project_root)
    previous_local_hooks_path = _local_hooks_path(project_root) if with_hooks and (project_root / ".git").exists() else None

    try:
        changes = _copy_runtime(project_root)

        if with_agent_rules:
            for agent in requested_agents:
                template_name, target_name = agent_targets[agent]
                block = (assets / "adapters" / template_name).read_text(encoding="utf-8")
                action = append_managed_block_if_missing(project_root / target_name, block)
                if action:
                    changes.append(target_name)

        if with_hooks:
            hook_dir = project_root / ".githooks"
            for hook_name in ("post-commit", "pre-push", "post-merge", "post-rewrite"):
                target = hook_dir / hook_name
                action = _copy_managed_file(assets / "hooks" / hook_name, target)
                executable = bool(target.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
                if action or not executable:
                    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    changes.append(f".githooks/{hook_name}")
            if (project_root / ".git").exists() and not hooks_path:
                result = subprocess.run(
                    ["git", "config", "core.hooksPath", ".githooks"],
                    cwd=project_root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if result.returncode != 0:
                    raise InstallConflict(result.stderr.strip() or "Could not configure core.hooksPath")

        if with_github_action:
            workflow = project_root / ".github" / "workflows" / "codebase-analysis-ai.yml"
            action = _copy_managed_file(
                assets / "workflows" / "codebase-analysis-ai.yml",
                workflow,
                {"__DEFAULT_BRANCH__": _detect_default_branch(project_root)},
            )
            if action:
                changes.append(".github/workflows/codebase-analysis-ai.yml")

        return sorted(set(changes))
    except Exception as exc:
        rollback_errors: list[str] = []
        try:
            _restore_files(snapshot)
            _remove_created_directories(created_directories)
        except Exception as rollback_exc:
            rollback_errors.append(f"files: {rollback_exc}")
        if with_hooks and (project_root / ".git").exists():
            try:
                _restore_hooks_path(project_root, previous_local_hooks_path)
            except Exception as rollback_exc:
                rollback_errors.append(f"Git configuration: {rollback_exc}")
        if rollback_errors:
            raise InstallConflict(
                f"Installation failed ({exc}); rollback incomplete ({'; '.join(rollback_errors)})"
            ) from exc
        raise
