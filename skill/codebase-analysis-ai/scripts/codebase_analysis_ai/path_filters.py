"""Shared repository path filters used by discovery and documentation checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


DEFAULT_EXCLUDED_PARTS = {
    ".git",
    ".agents",
    ".codex",
    ".claude",
    ".gemini",
    ".cursor",
    ".windsurf",
    ".vscode",
    ".idea",
    ".zed",
    ".devcontainer",
    ".github/agents",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".gradle",
    ".turbo",
    ".next",
    ".nuxt",
    ".angular",
    ".svelte-kit",
    "vendor",
    "target",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    "out",
    "bin",
    "obj",
    "tmp",
    "logs",
    "__pycache__",
}

DEFAULT_EXCLUDED_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "copilot-instructions.md",
}


def is_excluded_path(parts: tuple[str, ...]) -> bool:
    """Return whether a repository-relative path belongs to an excluded tree."""
    return (
        bool(DEFAULT_EXCLUDED_PARTS.intersection(parts))
        or parts[:2] == ("docs", "_archive")
        or parts[:2] == (".github", "agents")
        or (parts and parts[-1] in DEFAULT_EXCLUDED_FILES)
        or parts == (".github", "copilot-instructions.md")
    )


def iter_repository_files(root: Path) -> Iterator[Path]:
    """Yield files under ``root`` while pruning excluded directories early.

    ``os.walk`` is used with ``followlinks=False`` so directory symlinks are
    never traversed. Excluded directories are removed from ``dirnames`` before
    they are descended into, keeping the cost proportional to the files that
    are actually inspected instead of the whole tree.
    """
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        try:
            relative_parts = current.relative_to(root).parts
        except ValueError:
            relative_parts = ()
        kept_directories: list[str] = []
        for name in dirnames:
            candidate_parts = relative_parts + (name,)
            if is_excluded_path(candidate_parts):
                continue
            if (current / name).is_symlink():
                continue
            kept_directories.append(name)
        dirnames[:] = kept_directories
        for filename in filenames:
            candidate_parts = relative_parts + (filename,)
            if is_excluded_path(candidate_parts):
                continue
            path = current / filename
            if path.is_file():
                yield path
