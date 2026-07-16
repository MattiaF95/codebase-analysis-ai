"""Detect existing repository documentation without reading its contents."""

from __future__ import annotations

from pathlib import Path

from .path_filters import is_excluded_path


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
def first_documentation_file(root: Path) -> Path | None:
    """Return the first documentation file found, without opening it."""
    candidates = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded_path(path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in DOCUMENTATION_SUFFIXES and path.stem.lower() not in DOCUMENTATION_NAMES:
            continue
        candidates.append(path)

    root_readmes = [
        path for path in candidates
        if path.parent == root and path.name.casefold() == "readme.md"
    ]
    if root_readmes:
        return min(root_readmes, key=lambda path: path.name.casefold())
    return min(candidates) if candidates else None
