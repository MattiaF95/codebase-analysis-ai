"""Detect existing repository documentation without reading its contents."""

from __future__ import annotations

from pathlib import Path


DOCUMENTATION_SUFFIXES = {
    ".md", ".markdown", ".mdx", ".pdf",
    ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".odt", ".ods", ".odp", ".rtf", ".txt", ".rst", ".adoc",
    ".tex", ".html", ".htm",
}
DOCUMENTATION_NAMES = {
    "readme", "license", "copying", "changelog", "contributing",
    "code_of_conduct", "security", "support",
}
DEFAULT_EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "target",
    "dist",
    "build",
    "__pycache__",
}


def first_documentation_file(root: Path) -> Path | None:
    """Return the first documentation file found, without opening it."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in DOCUMENTATION_SUFFIXES and path.stem.lower() not in DOCUMENTATION_NAMES:
            continue
        if DEFAULT_EXCLUDED_PARTS.intersection(path.relative_to(root).parts):
            continue
        return path
    return None
