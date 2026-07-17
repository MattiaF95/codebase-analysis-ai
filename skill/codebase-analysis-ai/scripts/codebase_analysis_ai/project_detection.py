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

    backend_detected = "pom.xml" in names or any(name.endswith(".gradle") for name in names)
    if backend_detected:
        areas.append("backend")
        technologies.append("Java/JVM")
    if "package.json" in names:
        technologies.append("Node.js")
    if "angular.json" in names:
        areas.append("frontend")
        technologies.append("Angular")
    elif any(path.endswith((".tsx", ".jsx")) for path in files):
        areas.append("frontend")
    html_files = [path for path in files if path.endswith((".html", ".htm"))]
    css_files = [path for path in files if path.endswith((".css", ".scss", ".sass", ".less"))]
    js_files = [path for path in files if path.endswith((".js", ".mjs"))]
    html_at_site_root = any(
        len(Path(path).parts) == 1 or Path(path).parts[0].lower() in {"public", "site", "static", "web", "src", "app"}
        for path in html_files
    )
    if html_files and not backend_detected and (html_at_site_root or css_files or js_files):
        areas.append("static-site")
        technologies.append("HTML")
        if css_files:
            technologies.append("CSS")
        if js_files:
            technologies.append("JavaScript")
    if any(path.endswith(".sql") or "/migrations/" in f"/{path}/" for path in files):
        areas.append("database")
    if any(Path(path).name.startswith("Dockerfile") or "docker-compose" in path for path in files):
        areas.append("infrastructure")
        technologies.append("Docker")
    if any(path.startswith((".github/workflows/", ".gitlab-ci")) for path in files):
        areas.append("infrastructure")
    if any("service" in part.lower() for path in files for part in Path(path).parts[:2]):
        areas.append("services")

    topic_paths: dict[str, list[str]] = {}
    architecture_paths = sorted(path for path in files if (
        Path(path).name.lower() in {
            "readme.md", "package.json", "pom.xml", "build.gradle", "settings.gradle",
            "dockerfile", "docker-compose.yml", "docker-compose.yaml", "angular.json",
        } or path.startswith(".github/workflows/")
    ))
    if len(set(areas)) > 1 and architecture_paths:
        topic_paths["architecture"] = architecture_paths[:20]
    test_paths = sorted(path for path in files if any(
        marker in {part.lower() for part in Path(path).parts} for marker in {"test", "tests", "spec", "specs"}
    ) or Path(path).name.lower().startswith(("test_", "spec_")) or ".test." in Path(path).name.lower())
    if test_paths:
        topic_paths["testing"] = test_paths[:20]
    security_paths = sorted(path for path in files if any(
        token in part.lower() for part in Path(path).parts for token in {"auth", "security", "permission", "policy", "identity"}
    ))
    if security_paths:
        topic_paths["security"] = security_paths[:20]
    deployment_paths = sorted(path for path in files if "docker" in path.lower() or "deploy" in path.lower() or ".github/workflows/" in path)
    if deployment_paths:
        topic_paths["deployment"] = deployment_paths[:20]
    if "static-site" in areas:
        seo_paths = sorted(path for path in files if any(token in Path(path).name.lower() for token in {"robots", "sitemap", "seo"}))
        if seo_paths or html_files:
            topic_paths["seo"] = (seo_paths or html_files)[:20]

    def source_areas_for(paths: list[str]) -> list[str]:
        inferred: set[str] = set()
        for path in paths:
            parts = {part.lower() for part in Path(path).parts}
            for area in set(areas):
                if area.lower() in parts:
                    inferred.add(area)
            if "static-site" in areas and Path(path).suffix.lower() in {
                ".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".mjs"
            }:
                inferred.add("static-site")
        return sorted(inferred)

    topic_reasons = {
        "architecture": "multiple source areas plus detected project boundary files",
        "deployment": "deployment, container, or workflow paths",
        "security": "security-related path names",
        "seo": "HTML or SEO-related file names in a static site",
        "testing": "test or spec paths",
    }
    topics = [
        {
            "topic": topic,
            "candidatePaths": paths,
            "sourceAreas": sorted(set(areas)) if topic == "architecture" else source_areas_for(paths),
            "reason": topic_reasons[topic],
        }
        for topic, paths in sorted(topic_paths.items())
    ]

    return {
        "areas": sorted(set(areas)),
        "technologies": sorted(set(technologies)),
        "documentationTopics": topics,
        "fileCount": len(files),
    }
