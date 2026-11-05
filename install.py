#!/usr/bin/env python3
"""Install Codebase Analysis AI for one or more supported agents."""

from __future__ import annotations

import argparse
import shutil
import stat
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent
SKILL_SOURCE = REPOSITORY_ROOT / "skill" / "codebase-analysis-ai"
sys.path.insert(0, str(SKILL_SOURCE / "scripts"))

from codebase_analysis_ai.project_installer import (  # noqa: E402
    install_project_components,
    preflight_project_components,
)


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


def _skill_source_files() -> list[Path]:
    return [
        source
        for source in SKILL_SOURCE.rglob("*")
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
    ]


def _preflight_skill(target: Path) -> list[Path]:
    """Validate a skill target without changing the filesystem."""
    source_files = _skill_source_files()
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
    return source_files


def install_skill(target: Path, source_files: list[Path] | None = None) -> None:
    source_files = _preflight_skill(target) if source_files is None else source_files
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    for source in source_files:
        destination_path = target / source.relative_to(SKILL_SOURCE)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination_path)


def _snapshot_skill(
    target: Path,
    source_files: list[Path],
    boundary: Path,
) -> tuple[dict[Path, tuple[bytes, int] | None], list[Path]]:
    """Capture skill files and directories the installation may create or change."""
    snapshot: dict[Path, tuple[bytes, int] | None] = {}
    for source in source_files:
        destination_path = target / source.relative_to(SKILL_SOURCE)
        if destination_path.is_file():
            snapshot[destination_path] = (
                destination_path.read_bytes(),
                stat.S_IMODE(destination_path.stat().st_mode),
            )
        else:
            snapshot[destination_path] = None

    missing_directories: set[Path] = set()
    for destination_path in snapshot:
        parent = destination_path.parent
        while parent != boundary and boundary in parent.parents:
            if not parent.exists():
                missing_directories.add(parent)
            parent = parent.parent
    if target != boundary and not target.exists():
        missing_directories.add(target)
    return snapshot, sorted(missing_directories, key=lambda path: len(path.parts), reverse=True)


def _restore_skill(
    snapshot: dict[Path, tuple[bytes, int] | None],
    directories: list[Path],
) -> None:
    for destination_path, previous in snapshot.items():
        if previous is None:
            if destination_path.is_file() or destination_path.is_symlink():
                destination_path.unlink()
            continue
        content, mode = previous
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(content)
        destination_path.chmod(mode)
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            # Keep a directory populated by another process or a manual action.
            continue


def _resolve_project_root(value: str) -> Path:
    path = Path(value)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError(f"Project root cannot be resolved: {value}") from exc
    if not resolved.is_dir():
        raise RuntimeError(f"Project root is not a directory: {resolved}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codebase Analysis AI")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--agent", nargs="+", default=["codex"], choices=[*AGENTS, "all"])
    parser.add_argument("--scope", choices=["project", "user"], default="project")
    args = parser.parse_args()

    try:
        project_root = _resolve_project_root(args.project_root)
        agents = list(AGENTS) if "all" in args.agent else list(dict.fromkeys(args.agent))
        targets: list[Path] = []
        target_agents: dict[Path, str] = {}
        for agent in agents:
            target = destination(agent, args.scope, project_root)
            if target not in target_agents:
                targets.append(target)
                target_agents[target] = agent

        skill_sources = {target: _preflight_skill(target) for target in targets}
        if args.scope == "project":
            preflight_project_components(project_root, agents, True, True, True)
    except (RuntimeError, OSError) as exc:
        print(f"Codebase Analysis AI setup stopped: {exc}", file=sys.stderr)
        return 2

    boundary = Path.home().resolve() if args.scope == "user" else project_root
    snapshots: list[tuple[dict[Path, tuple[bytes, int] | None], list[Path]]] = []
    try:
        for target in targets:
            snapshot, directories = _snapshot_skill(target, skill_sources[target], boundary)
            snapshots.append((snapshot, directories))
            install_skill(target, skill_sources[target])
            print(f"Installed skill for {target_agents[target]}: {target}")

        if args.scope == "project":
            changed = install_project_components(project_root, agents, True, True, True)
            for path in changed:
                print(f"Configured: {path}")
    except (RuntimeError, OSError) as exc:
        rollback_errors: list[str] = []
        for snapshot, directories in reversed(snapshots):
            try:
                _restore_skill(snapshot, directories)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        message = f"Codebase Analysis AI setup stopped: {exc}"
        if rollback_errors:
            message += f" (skill rollback incomplete: {'; '.join(rollback_errors)})"
        print(message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
