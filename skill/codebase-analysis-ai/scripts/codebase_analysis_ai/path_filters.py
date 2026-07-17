"""Shared repository path filters used by discovery and documentation checks."""

from __future__ import annotations


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
    "vendor",
    "target",
    "dist",
    "build",
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
