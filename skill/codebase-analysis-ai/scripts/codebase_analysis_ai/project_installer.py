"""Install managed Codebase Analysis AI components into a target repository."""

from __future__ import annotations

import shutil
import stat
import subprocess
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
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated, encoding="utf-8")
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
        target.write_text(updated, encoding="utf-8")
        return "updated"
    if START in existing:
        raise InstallConflict(f"Refusing to modify incomplete managed block: {target}")
    separator = "\n\n" if existing.strip() else ""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(existing.rstrip() + separator + block.strip() + "\n", encoding="utf-8")
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
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return action


def _preflight_runtime(project_root: Path) -> None:
    check = project_root / "tools" / "codebase-analysis-ai" / "check.py"
    if check.exists() and (
        not check.is_file()
        or RUNTIME_MARKER not in check.read_text(encoding="utf-8", errors="replace")
    ):
        raise InstallConflict(f"Refusing to overwrite unmanaged runtime: {check}")


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
        shutil.copy2(source_check, check)
        changes.append("tools/codebase-analysis-ai/check.py")
    package_destination = destination / "codebase_analysis_ai"
    package_destination.mkdir(parents=True, exist_ok=True)
    for source in (source_scripts / "codebase_analysis_ai").rglob("*"):
        if not source.is_file() or source.suffix in {".pyc"} or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(source_scripts / "codebase_analysis_ai")
        target = package_destination / relative
        if not target.exists() or target.read_bytes() != source.read_bytes():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
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
