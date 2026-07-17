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


def _copy_managed_file(source: Path, target: Path, replacements: dict[str, str] | None = None) -> str:
    content = source.read_text(encoding="utf-8")
    for old, new in (replacements or {}).items():
        content = content.replace(old, new)
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if MANAGED not in existing:
            raise InstallConflict(f"Refusing to overwrite unmanaged file: {target}")
        action = "updated"
    else:
        action = "created"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return action


def _ensure_managed_file(source: Path, target: Path, replacements: dict[str, str] | None = None) -> str | None:
    """Create an optional file, preserving every existing file."""
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if MANAGED not in existing:
            raise InstallConflict(f"Refusing to overwrite unmanaged file: {target}")
        return None
    return _copy_managed_file(source, target, replacements)


def _copy_runtime(project_root: Path) -> list[str]:
    source_scripts = skill_root() / "scripts"
    destination = project_root / "tools" / "codebase-analysis-ai"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_scripts / "codebase_analysis_ai.py", destination / "check.py")
    package_destination = destination / "codebase_analysis_ai"
    if package_destination.exists():
        shutil.rmtree(package_destination)
    shutil.copytree(source_scripts / "codebase_analysis_ai", package_destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return ["tools/codebase-analysis-ai/check.py", "tools/codebase-analysis-ai/codebase_analysis_ai/"]


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
    changes = _copy_runtime(project_root)

    agent_targets = {
        "codex": ("AGENTS.md", "AGENTS.md"),
        "claude": ("CLAUDE.md", "CLAUDE.md"),
        "gemini": ("GEMINI.md", "GEMINI.md"),
        "copilot": ("copilot-instructions.md", ".github/copilot-instructions.md"),
    }
    if with_agent_rules:
        for agent in dict.fromkeys(agents):
            template_name, target_name = agent_targets[agent]
            block = (assets / "adapters" / template_name).read_text(encoding="utf-8")
            update_managed_block(project_root / target_name, block)
            changes.append(target_name)

    if with_hooks:
        hook_dir = project_root / ".githooks"
        for hook_name in ("post-commit", "pre-push", "post-merge", "post-rewrite"):
            target = hook_dir / hook_name
            action = _ensure_managed_file(assets / "hooks" / hook_name, target)
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            if action:
                changes.append(f".githooks/{hook_name}")
        if (project_root / ".git").exists():
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
        action = _ensure_managed_file(
            assets / "workflows" / "codebase-analysis-ai.yml",
            workflow,
            {"__DEFAULT_BRANCH__": _detect_default_branch(project_root)},
        )
        if action:
            changes.append(".github/workflows/codebase-analysis-ai.yml")

    return sorted(set(changes))
