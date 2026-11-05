"""Read, validate, and query the source-to-document map."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .document_kinds import document_kind, section_contract_errors
from .glob_patterns import glob_match
from .path_filters import is_excluded_path


DEFAULT_IGNORE = [
    ".git/**",
    ".githooks/**",
    "**/AGENTS.md",
    "**/CLAUDE.md",
    "**/GEMINI.md",
    ".github/copilot-instructions.md",
    "**/copilot-instructions.md",
    ".github/agents/**",
    ".github/workflows/codebase-analysis-ai.yml",
    "docs/**",
    "tools/codebase-analysis-ai/**",
    "node_modules/**",
    "**/node_modules/**",
    "target/**",
    "**/target/**",
    "dist/**",
    "**/dist/**",
    "build/**",
    "**/build/**",
    "__pycache__/**",
    "**/__pycache__/**",
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.jks",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.jks",
]

RELEVANT_SUFFIXES = {
    # Application languages already covered.
    ".java", ".kt", ".kts", ".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".rs",
    ".cs", ".php", ".rb", ".swift", ".scala", ".sql", ".graphql", ".proto", ".xml",
    ".yml", ".yaml", ".json", ".toml", ".properties", ".gradle", ".sh", ".ps1",
    # Infrastructure as code and deployment descriptors.
    ".tf", ".tfvars", ".hcl", ".bicep", ".nix",
    # Mobile and embedded sources.
    ".dart", ".m", ".mm", ".ino",
    # Frontend components and static assets.
    ".vue", ".svelte", ".astro", ".html", ".htm", ".css", ".scss", ".less",
    ".sass", ".styl",
    # Build and runtime configuration files.
    ".ini", ".cfg", ".conf",
}

# Compared case-insensitively against the file name.
RELEVANT_NAMES = {
    "dockerfile", "containerfile", "caddyfile", "procfile", "nginx.conf",
    "kustomization.yaml", "kustomization.yml", "chart.yaml", "values.yaml",
    "makefile", "pom.xml", "package.json", "angular.json", "settings.gradle",
    "build.gradle", "docker-compose.yml", "docker-compose.yaml",
}

# Lockfiles are dependency metadata and are never reported as unmapped sources.
LOCKFILE_NAMES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "cargo.lock",
    "poetry.lock",
    "pipfile.lock",
    "composer.lock",
    "gemfile.lock",
    "go.sum",
    "flake.lock",
}

# Generated artifacts keep a source-like suffix but are not hand-written code.
GENERATED_OUTPUT_PATTERNS = (
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.g.dart",
    "*.freezed.dart",
    "*.pb.go",
    "*_pb2.py",
)


def _is_generated_or_lockfile(name: str) -> bool:
    lowered = name.casefold()
    if lowered in LOCKFILE_NAMES:
        return True
    return any(glob_match(lowered, pattern) for pattern in GENERATED_OUTPUT_PATTERNS)


LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|[0-9]{3}))?$")
LANGUAGE_DECISION_SOURCES = {"user", "repository-policy", "existing-canonical-docs"}
WINDOWS_DRIVE_PATH = re.compile(r"^[A-Za-z]:/")


class MapError(RuntimeError):
    pass


def normalize_repository_path(value: str) -> str:
    """Return one canonical repository-relative path or pattern."""
    if not isinstance(value, str) or not value:
        raise MapError("path must be a non-empty string")
    normalized = value.replace("\\", "/")
    if "\x00" in normalized or normalized.startswith("/") or WINDOWS_DRIVE_PATH.match(normalized):
        raise MapError(f"path must be repository-relative: {value}")
    if any(part in {"", ".."} for part in normalized.split("/")):
        raise MapError(f"path contains an invalid segment: {value}")
    return PurePosixPath(normalized).as_posix()


def resolve_repository_path(root: Path, value: str) -> Path:
    """Resolve a repository path without allowing lexical or symlink escapes."""
    repository = root.resolve()
    resolved = (repository / normalize_repository_path(value)).resolve()
    try:
        resolved.relative_to(repository)
    except ValueError as exc:
        raise MapError(f"path escapes repository: {value}") from exc
    return resolved


def _structure_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        errors.append("settings must be an object")
    else:
        value = settings.get("ignorePatterns", [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append("settings.ignorePatterns must be a string array")
        else:
            for index, pattern in enumerate(value):
                try:
                    normalize_repository_path(pattern)
                except MapError as exc:
                    errors.append(f"settings.ignorePatterns[{index}]: {exc}")
    documents = data.get("documents", {})
    if not isinstance(documents, dict):
        errors.append("documents must be an object")
        return errors
    for doc_id, document in documents.items():
        if not isinstance(doc_id, str) or not doc_id:
            errors.append("document IDs must be non-empty strings")
            continue
        if not isinstance(document, dict):
            errors.append(f"{doc_id}: document must be an object")
            continue
        source_hashes = document.get("sourceHashes", {})
        if not isinstance(source_hashes, dict) or not all(
            isinstance(path, str) and isinstance(digest, str) for path, digest in source_hashes.items()
        ):
            errors.append(f"{doc_id}: sourceHashes must be a string map")
        for key in ("sourcePatterns", "relatedDocuments"):
            value = document.get(key, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"{doc_id}: {key} must be a string array")
        kind = document.get("documentKind")
        sections = document.get("sections")
        if kind is not None:
            if not isinstance(kind, str) or not kind:
                errors.append(f"{doc_id}.documentKind must be a non-empty string")
            elif document_kind(kind) is None:
                errors.append(f"{doc_id}.documentKind: unknown document kind {kind!r}")
        if sections is not None:
            if kind is None:
                errors.append(f"{doc_id}.sections requires documentKind")
            else:
                for issue in section_contract_errors(kind, sections):
                    errors.append(f"{doc_id}.sections: {issue}")
        metadata = document.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{doc_id}.metadata must be an object")
    return errors


@dataclass
class DocumentationMap:
    path: Path
    data: dict[str, Any]

    @property
    def documents(self) -> dict[str, dict[str, Any]]:
        documents = self.data.setdefault("documents", {})
        return documents if isinstance(documents, dict) else {}

    @property
    def settings(self) -> dict[str, Any]:
        settings = self.data.setdefault("settings", {})
        return settings if isinstance(settings, dict) else {}

    @property
    def taxonomy(self) -> dict[str, Any]:
        taxonomy = self.data.get("taxonomy")
        return taxonomy if isinstance(taxonomy, dict) else {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def validate(self) -> list[str]:
        errors = _structure_errors(self.data)

        def checked_path(label: str, value: object) -> str | None:
            if not isinstance(value, str):
                return None
            try:
                return normalize_repository_path(value)
            except MapError as exc:
                errors.append(f"{label}: {exc}")
                return None

        if self.data.get("schemaVersion") != 1:
            errors.append("documentation-map.json must use schemaVersion 1")
        language = self.settings.get("documentationLanguage")
        decision_source = self.settings.get("languageDecisionSource")
        if bool(language) != bool(decision_source):
            errors.append("settings must define documentationLanguage and languageDecisionSource together")
        if language and (not isinstance(language, str) or not LANGUAGE_TAG.fullmatch(language)):
            errors.append("settings.documentationLanguage must use a supported BCP 47 language tag")
        if decision_source and decision_source not in LANGUAGE_DECISION_SOURCES:
            errors.append(
                "settings.languageDecisionSource must be user, repository-policy, or existing-canonical-docs"
            )
        paths: dict[str, str] = {}
        taxonomy = self.data.get("taxonomy")
        if taxonomy is not None:
            if not isinstance(taxonomy, dict):
                errors.append("taxonomy must be an object")
            else:
                source_areas = taxonomy.get("sourceAreas", {})
                topics = taxonomy.get("documentationTopics", [])
                if not isinstance(source_areas, dict):
                    errors.append("taxonomy.sourceAreas must be an object")
                    source_areas = {}
                elif not source_areas:
                    errors.append("taxonomy.sourceAreas must define at least one approved source area")
                if not isinstance(topics, list):
                    errors.append("taxonomy.documentationTopics must be an array")
                    topics = []
                for area_id, area in source_areas.items():
                    if not isinstance(area, dict):
                        errors.append(f"taxonomy.sourceAreas.{area_id} must be an object")
                        continue
                    candidate_paths = area.get("candidatePaths")
                    evidence = area.get("evidence")
                    reason = area.get("reason")
                    if not isinstance(candidate_paths, list) or not candidate_paths or not all(
                        isinstance(path, str) and path for path in candidate_paths
                    ):
                        errors.append(f"taxonomy.sourceAreas.{area_id}.candidatePaths must be a non-empty string array")
                    else:
                        for index, candidate in enumerate(candidate_paths):
                            checked_path(f"taxonomy.sourceAreas.{area_id}.candidatePaths[{index}]", candidate)
                    if not isinstance(evidence, list) or not evidence or not all(
                        isinstance(path, str) and path for path in evidence
                    ):
                        errors.append(f"taxonomy.sourceAreas.{area_id}.evidence must be a non-empty string array")
                    else:
                        for index, evidence_path in enumerate(evidence):
                            checked_path(f"taxonomy.sourceAreas.{area_id}.evidence[{index}]", evidence_path)
                    if not isinstance(reason, str) or not reason:
                        errors.append(f"taxonomy.sourceAreas.{area_id}.reason must be a non-empty string")
                for index, topic in enumerate(topics):
                    if not isinstance(topic, dict):
                        errors.append(f"taxonomy.documentationTopics[{index}] must be an object")
                        continue
                    topic_name = topic.get("topic")
                    candidate_paths = topic.get("candidatePaths")
                    source_area_ids = topic.get("sourceAreas")
                    reason = topic.get("reason")
                    if not isinstance(topic_name, str) or not topic_name:
                        errors.append(f"taxonomy.documentationTopics[{index}].topic must be a non-empty string")
                    if not isinstance(candidate_paths, list) or not candidate_paths or not all(
                        isinstance(path, str) and path for path in candidate_paths
                    ):
                        errors.append(
                            f"taxonomy.documentationTopics[{index}].candidatePaths must be a non-empty string array"
                        )
                    else:
                        for path_index, candidate in enumerate(candidate_paths):
                            checked_path(
                                f"taxonomy.documentationTopics[{index}].candidatePaths[{path_index}]",
                                candidate,
                            )
                    if not isinstance(source_area_ids, list) or not all(
                        isinstance(area_id, str) and area_id for area_id in source_area_ids
                    ):
                        errors.append(f"taxonomy.documentationTopics[{index}].sourceAreas must be a string array")
                        source_area_ids = []
                    if not isinstance(reason, str) or not reason:
                        errors.append(f"taxonomy.documentationTopics[{index}].reason must be a non-empty string")
                    for area_id in source_area_ids:
                        if area_id not in source_areas:
                            errors.append(
                                f"taxonomy.documentationTopics[{index}]: unknown source area {area_id}"
                            )
        for doc_id, document in self.documents.items():
            path = document.get("path")
            if not isinstance(path, str) or not path:
                errors.append(f"{doc_id}: missing path")
            else:
                normalized_path = checked_path(f"{doc_id}.path", path)
                if normalized_path in paths:
                    errors.append(f"{doc_id}: duplicate path also used by {paths[normalized_path]}")
                elif normalized_path is not None:
                    paths[normalized_path] = doc_id
            source_paths: dict[str, str] = {}
            source_hashes = document.get("sourceHashes", {})
            if isinstance(source_hashes, dict):
                for source_path in source_hashes:
                    normalized_source = checked_path(f"{doc_id}.sourceHashes[{source_path!r}]", source_path)
                    if normalized_source in source_paths:
                        errors.append(
                            f"{doc_id}: duplicate source hash path also used by {source_paths[normalized_source]}"
                        )
                    elif normalized_source is not None:
                        source_paths[normalized_source] = source_path
            source_patterns = document.get("sourcePatterns", [])
            if isinstance(source_patterns, list):
                for index, pattern in enumerate(source_patterns):
                    checked_path(f"{doc_id}.sourcePatterns[{index}]", pattern)
            for related in document.get("relatedDocuments", []):
                if related not in self.documents:
                    errors.append(f"{doc_id}: unknown related document {related}")
        return errors

    def ignore_patterns(self) -> list[str]:
        return [*DEFAULT_IGNORE, *self.settings.get("ignorePatterns", [])]

    def is_ignored(self, path: str) -> bool:
        normalized = normalize_repository_path(path)
        if is_excluded_path(PurePosixPath(normalized).parts):
            return True
        return any(glob_match(normalized, pattern) for pattern in self.ignore_patterns())

    def is_relevant_source(self, path: str) -> bool:
        if self.is_ignored(path):
            return False
        pure = PurePosixPath(normalize_repository_path(path))
        if _is_generated_or_lockfile(pure.name):
            return False
        return pure.name.casefold() in RELEVANT_NAMES or pure.suffix.lower() in RELEVANT_SUFFIXES

    def is_document_path(self, path: str) -> bool:
        normalized = normalize_repository_path(path)
        registered = {
            normalize_repository_path(str(document.get("path", "")))
            for document in self.documents.values()
            if isinstance(document, dict) and document.get("path")
        }
        if normalized in registered:
            return True
        return (
            normalized.startswith("docs/")
            and normalized.endswith(".md")
            and not normalized.startswith(DOCUMENTATION_EXEMPT_PREFIXES)
        )

    def matching_documents(self, source_path: str) -> set[str]:
        normalized = normalize_repository_path(source_path)
        matched: set[str] = set()
        for doc_id, document in self.documents.items():
            explicit = {normalize_repository_path(item) for item in document.get("sourceHashes", {})}
            patterns = [normalize_repository_path(item) for item in document.get("sourcePatterns", [])]
            if normalized in explicit or any(glob_match(normalized, pattern) for pattern in patterns):
                matched.add(doc_id)
        return matched

    def recorded_hash(self, doc_id: str, source_path: str) -> str | None:
        normalized = normalize_repository_path(source_path)
        for path, digest in self.documents[doc_id].get("sourceHashes", {}).items():
            if normalize_repository_path(path) == normalized:
                return digest
        return None

    def set_recorded_hash(self, doc_id: str, source_path: str, digest: str) -> None:
        normalized = normalize_repository_path(source_path)
        hashes = self.documents[doc_id].setdefault("sourceHashes", {})
        for path in list(hashes):
            if normalize_repository_path(path) == normalized and path != normalized:
                del hashes[path]
        hashes[normalized] = digest


DOCUMENTATION_INDEX = "docs/index.md"
DECISION_DIRECTORY = "docs/decisions/"
LEGACY_DECISION_DIRECTORY = "docs/adr/"
ANALYSIS_DIRECTORY = "docs/_analysis/"
DOCUMENTATION_EXEMPT_PREFIXES = ("docs/_meta/", "docs/_archive/", ANALYSIS_DIRECTORY)


@dataclass(frozen=True)
class DocumentationIssues:
    missing: tuple[str, ...] = ()
    unregistered: tuple[str, ...] = ()
    index: tuple[str, ...] = ()

    @property
    def errors(self) -> tuple[str, ...]:
        return (
            *(f"Missing document: {path}" for path in self.missing),
            *(f"Unregistered document: {path}" for path in self.unregistered),
            *self.index,
        )


def registered_document_paths(documentation_map: DocumentationMap) -> set[str]:
    """Return the canonical path of every document recorded in the map."""
    registered: set[str] = set()
    for document in documentation_map.documents.values():
        if not isinstance(document, dict):
            continue
        path = document.get("path")
        if not isinstance(path, str) or not path:
            continue
        try:
            registered.add(normalize_repository_path(path))
        except MapError:
            continue
    return registered


def active_document_paths(root: Path) -> list[str]:
    """List active Markdown documents under docs/, excluding metadata and archives."""
    docs = root / "docs"
    if not docs.is_dir():
        return []
    documents: list[str] = []
    for candidate in docs.rglob("*.md"):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(root).as_posix()
        if relative.startswith(DOCUMENTATION_EXEMPT_PREFIXES):
            continue
        documents.append(relative)
    return sorted(documents)


def documentation_issues(root: Path, documentation_map: DocumentationMap) -> DocumentationIssues:
    """Validate document existence, index registration and map coverage."""
    registered = registered_document_paths(documentation_map)
    missing = tuple(
        path
        for path in sorted(registered)
        if not (root / path).is_file()
    )
    index_path = root / DOCUMENTATION_INDEX
    index_exists = index_path.is_file()
    index_errors: list[str] = []
    if index_exists and DOCUMENTATION_INDEX not in registered:
        index_errors.append(f"Unregistered documentation index: {DOCUMENTATION_INDEX}")
    active = active_document_paths(root)
    if not index_exists and active:
        index_errors.append(f"Missing documentation index: {DOCUMENTATION_INDEX}")
    unregistered = tuple(
        path
        for path in active
        if path not in registered and path != DOCUMENTATION_INDEX
    )
    return DocumentationIssues(missing, unregistered, tuple(index_errors))


def load_map(root: Path) -> DocumentationMap:
    path = root / "docs" / "_meta" / "documentation-map.json"
    if not path.is_file():
        raise MapError(f"Documentation map not found: {path.relative_to(root)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise MapError(f"Cannot read documentation map: {exc}") from exc
    if not isinstance(data, dict):
        raise MapError("documentation-map.json must contain a JSON object")
    structure_errors = _structure_errors(data)
    if structure_errors:
        raise MapError("Invalid documentation map: " + "; ".join(structure_errors))
    return DocumentationMap(path=path, data=data)
