"""Detect existing repository documentation without reading its contents."""

from __future__ import annotations

from pathlib import Path

from .path_filters import iter_repository_files


DOCUMENTATION_SUFFIXES = {
    ".md", ".markdown", ".mdx", ".pdf",
    ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".odt", ".ods", ".odp", ".rtf", ".txt", ".rst", ".adoc",
    ".tex", ".html", ".htm",
}

# HTML and plain text are common web/source assets. They only count as
# documentation when they live at the repository root, in a documentation
# directory, or use a canonical documentation file name.
PATH_SCOPED_SUFFIXES = {".html", ".htm", ".txt"}
DOCUMENTATION_DIRECTORY_NAMES = {
    "docs", "doc", "documentation", "manual", "manuals",
    "guide", "guides", "wiki",
}
DOCUMENTATION_NAMES = {
    "readme", "license", "copying", "changelog", "contributing",
    "code_of_conduct", "security", "support",
}


def _is_documentation_path(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    suffix = path.suffix.lower()
    stem = path.stem.casefold()

    if stem in DOCUMENTATION_NAMES and (not suffix or suffix in DOCUMENTATION_SUFFIXES):
        return True
    if suffix not in DOCUMENTATION_SUFFIXES:
        return False
    if suffix not in PATH_SCOPED_SUFFIXES:
        return True
    if len(relative.parts) == 1:
        return True
    return any(
        part.casefold() in DOCUMENTATION_DIRECTORY_NAMES
        for part in relative.parts[:-1]
    )


def first_documentation_file(root: Path) -> Path | None:
    """Return the first documentation file found, without opening it."""
    root = Path(root)
    if not root.is_absolute():
        root = root.absolute()

    candidates = [
        path
        for path in iter_repository_files(root)
        if _is_documentation_path(root, path)
    ]

    root_readmes = [
        path for path in candidates
        if path.parent == root and path.stem.casefold() == "readme"
    ]
    if root_readmes:
        return min(root_readmes, key=lambda path: path.name.casefold())
    return min(candidates) if candidates else None
