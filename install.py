#!/usr/bin/env python3
"""Install Codebase Analysis AI for one or more supported agents."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent
SKILL_SOURCE = REPOSITORY_ROOT / "skill" / "codebase-analysis-ai"
sys.path.insert(0, str(SKILL_SOURCE / "scripts"))

from codebase_analysis_ai.project_installer import install_project_components  # noqa: E402


AGENTS = ("codex", "claude", "gemini", "copilot")
MANAGED_SKILL_MARKER = "name: codebase-analysis-ai"


def destination(agent: str, scope: str, project_root: Path) -> Path:
    if scope == "user":
        base = Path.home()
        if agent == "claude":
            return base / ".claude" / "skills" / "codebase-analysis-ai"
        return base / ".agents" / "skills" / "codebase-analysis-ai"
    if agent == "claude":
        return project_root / ".claude" / "skills" / "codebase-analysis-ai"
    return project_root / ".agents" / "skills" / "codebase-analysis-ai"


def install_skill(target: Path) -> None:
    source_files = [
        source
        for source in SKILL_SOURCE.rglob("*")
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
    ]
    if target.is_symlink():
        raise RuntimeError(f"Refusing to replace symlinked skill target: {target}")
    if target.exists():
        if not target.is_dir():
            raise RuntimeError(f"Refusing to replace non-directory skill target: {target}")
        marker = target / "SKILL.md"
        if marker.is_symlink() or not marker.is_file() or MANAGED_SKILL_MARKER not in marker.read_text(
            encoding="utf-8", errors="replace"
        ):
            raise RuntimeError(f"Refusing to update unmanaged skill target: {target}")
    for source in source_files:
        destination_path = target / source.relative_to(SKILL_SOURCE)
        if destination_path.is_symlink() or (destination_path.exists() and not destination_path.is_file()):
            raise RuntimeError(f"Refusing to replace non-file skill target: {destination_path}")
        for parent in destination_path.parents:
            if parent == target:
                break
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise RuntimeError(f"Refusing to replace non-directory skill target: {parent}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    for source in source_files:
        destination_path = target / source.relative_to(SKILL_SOURCE)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codebase Analysis AI")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--agent", nargs="+", default=["codex"], choices=[*AGENTS, "all"])
    parser.add_argument("--scope", choices=["project", "user"], default="project")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    agents = list(AGENTS) if "all" in args.agent else list(dict.fromkeys(args.agent))
    installed: set[Path] = set()
    for agent in agents:
        target = destination(agent, args.scope, project_root)
        if target not in installed:
            install_skill(target)
            installed.add(target)
            print(f"Installed skill for {agent}: {target}")

    if args.scope == "project":
        changed = install_project_components(project_root, agents, True, True, True)
        for path in changed:
            print(f"Configured: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
