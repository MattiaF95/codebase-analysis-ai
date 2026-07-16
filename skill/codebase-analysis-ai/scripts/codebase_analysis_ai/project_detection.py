"""Detect common project areas without interpreting source code."""

from __future__ import annotations

from pathlib import Path

from .path_filters import is_excluded_path


def detect_areas(root: Path) -> dict[str, object]:
    files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not is_excluded_path(path.parts)
    }
    names = {Path(path).name for path in files}
    areas: list[str] = []
    technologies: list[str] = []

    if "pom.xml" in names or any(name.endswith(".gradle") for name in names):
        areas.append("backend")
        technologies.append("Java/JVM")
    if "package.json" in names:
        technologies.append("Node.js")
    if "angular.json" in names:
        areas.append("frontend")
        technologies.append("Angular")
    elif any(path.endswith((".tsx", ".jsx")) for path in files):
        areas.append("frontend")
    if any(path.endswith(".sql") or "/migrations/" in f"/{path}/" for path in files):
        areas.append("database")
    if any(Path(path).name.startswith("Dockerfile") or "docker-compose" in path for path in files):
        areas.append("infrastructure")
        technologies.append("Docker")
    if any(path.startswith((".github/workflows/", ".gitlab-ci")) for path in files):
        areas.append("infrastructure")
    if any("service" in part.lower() for path in files for part in Path(path).parts[:2]):
        areas.append("services")

    return {
        "areas": sorted(set(areas)),
        "technologies": sorted(set(technologies)),
        "fileCount": len(files),
    }
