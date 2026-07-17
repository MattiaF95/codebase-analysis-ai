"""Collect bounded structural repository evidence without interpreting architecture."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .path_filters import is_excluded_path


SCHEMA_VERSION = 2
MAX_ROOT_FILES = 50
MAX_SHALLOW_FILES = 150
MAX_STRUCTURAL_FILES = 100
MAX_SIGNAL_PATHS = 30
MAX_DIRECTORY_PATHS = 100
MAX_EXTENSION_TYPES = 100

STRUCTURAL_NAMES = {
    "angular.json",
    "build.gradle",
    "build.gradle.kts",
    "cargo.toml",
    "cmakelists.txt",
    "composer.json",
    "docker-compose.yaml",
    "docker-compose.yml",
    "gemfile",
    "go.mod",
    "makefile",
    "mix.exs",
    "package.json",
    "package.swift",
    "pom.xml",
    "pubspec.yaml",
    "pyproject.toml",
    "requirements.txt",
    "settings.gradle",
    "settings.gradle.kts",
    "workspace",
}

STRUCTURAL_SUFFIXES = {
    ".csproj",
    ".fsproj",
    ".sln",
    ".tf",
    ".vcxproj",
}

SENSITIVE_SUFFIXES = {".jks", ".key", ".p12", ".pem"}


def _is_readme(path: Path) -> bool:
    return path.stem.lower() == "readme"


def _is_structural_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name in STRUCTURAL_NAMES
        or name.startswith("dockerfile")
        or path.suffix.lower() in STRUCTURAL_SUFFIXES
        or _is_readme(path)
    )


def _is_sensitive_path(path: Path) -> bool:
    name = path.name.lower()
    return name == ".env" or name.startswith(".env.") or path.suffix.lower() in SENSITIVE_SUFFIXES


def _bounded(paths: list[str], limit: int) -> tuple[list[str], bool]:
    ordered = sorted(set(paths))
    return ordered[:limit], len(ordered) > limit


def inventory_project(root: Path) -> dict[str, object]:
    """Return path-only evidence for the parent agent's progressive analysis."""
    files = sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file()
        and not is_excluded_path(path.relative_to(root).parts)
        and not _is_sensitive_path(path.relative_to(root))
    )

    root_files, root_truncated = _bounded(
        [path.as_posix() for path in files if len(path.parts) == 1],
        MAX_ROOT_FILES,
    )
    shallow_files, shallow_truncated = _bounded(
        [path.as_posix() for path in files if len(path.parts) <= 2],
        MAX_SHALLOW_FILES,
    )
    structural_files, structural_truncated = _bounded(
        [path.as_posix() for path in files if _is_structural_file(path) and len(path.parts) <= 4],
        MAX_STRUCTURAL_FILES,
    )

    module_roots, module_roots_truncated = _bounded([
        path.parent.as_posix()
        for path in files
        if _is_structural_file(path)
        and not _is_readme(path)
        and 1 < len(path.parts) <= 4
        and path.parts[0] not in {".github", ".gitlab"}
    ], MAX_DIRECTORY_PATHS)
    top_level_directories, directories_truncated = _bounded(
        [path.parts[0] for path in files if len(path.parts) > 1],
        MAX_DIRECTORY_PATHS,
    )

    signal_candidates = {
        "deployment": [
            path.as_posix() for path in files
            if "deploy" in path.as_posix().lower()
            or "docker" in path.name.lower()
            or path.suffix.lower() == ".tf"
        ],
        "migrations": [
            path.as_posix() for path in files
            if "migrations" in {part.lower() for part in path.parts} or path.suffix.lower() == ".sql"
        ],
        "tests": [
            path.as_posix() for path in files
            if {"test", "tests", "spec", "specs"}.intersection(part.lower() for part in path.parts)
            or path.name.lower().startswith(("test_", "spec_"))
            or ".test." in path.name.lower()
        ],
        "workflows": [
            path.as_posix() for path in files
            if path.as_posix().startswith((".github/workflows/", ".gitlab-ci"))
        ],
    }
    signals: dict[str, list[str]] = {}
    signals_truncated = False
    for name, paths in sorted(signal_candidates.items()):
        signals[name], was_truncated = _bounded(paths, MAX_SIGNAL_PATHS)
        signals_truncated = signals_truncated or was_truncated

    extension_counts = Counter(path.suffix.lower() or "[no extension]" for path in files)
    extension_items = sorted(extension_counts.items())
    extensions_truncated = len(extension_items) > MAX_EXTENSION_TYPES
    return {
        "schemaVersion": SCHEMA_VERSION,
        "rootFiles": root_files,
        "shallowFiles": shallow_files,
        "topLevelDirectories": top_level_directories,
        "structuralFiles": structural_files,
        "moduleRoots": module_roots,
        "extensionCounts": dict(extension_items[:MAX_EXTENSION_TYPES]),
        "signals": signals,
        "fileCount": len(files),
        "truncated": any((
            root_truncated,
            shallow_truncated,
            structural_truncated,
            module_roots_truncated,
            directories_truncated,
            extensions_truncated,
            signals_truncated,
        )),
    }
