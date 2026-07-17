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
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SKILL_SOURCE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


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
