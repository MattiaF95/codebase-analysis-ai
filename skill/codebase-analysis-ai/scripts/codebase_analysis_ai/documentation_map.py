"""Read, validate, and query the source-to-document map."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


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
    "**/node_modules/**",
    "**/target/**",
    "**/dist/**",
    "**/build/**",
    "**/__pycache__/**",
    "**/.env",
    "**/.env.*",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.jks",
]

RELEVANT_SUFFIXES = {
    ".java", ".kt", ".kts", ".js", ".jsx", ".ts", ".tsx", ".py", ".go", ".rs",
    ".cs", ".php", ".rb", ".swift", ".scala", ".sql", ".graphql", ".proto", ".xml",
    ".yml", ".yaml", ".json", ".toml", ".properties", ".gradle", ".sh", ".ps1",
}

RELEVANT_NAMES = {
    "Dockerfile", "Makefile", "pom.xml", "package.json", "angular.json", "settings.gradle",
    "build.gradle", "docker-compose.yml", "docker-compose.yaml",
}

LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|[0-9]{3}))?$")
LANGUAGE_DECISION_SOURCES = {"user", "repository-policy", "existing-canonical-docs"}


class MapError(RuntimeError):
    pass


@dataclass
class DocumentationMap:
    path: Path
    data: dict[str, Any]

    @property
    def documents(self) -> dict[str, dict[str, Any]]:
        return self.data.setdefault("documents", {})

    @property
    def settings(self) -> dict[str, Any]:
        return self.data.setdefault("settings", {})

    @property
    def taxonomy(self) -> dict[str, Any]:
        taxonomy = self.data.get("taxonomy")
        return taxonomy if isinstance(taxonomy, dict) else {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def validate(self) -> list[str]:
        errors: list[str] = []
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
                    if not isinstance(evidence, list) or not evidence or not all(
                        isinstance(path, str) and path for path in evidence
                    ):
                        errors.append(f"taxonomy.sourceAreas.{area_id}.evidence must be a non-empty string array")
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
            if not path:
                errors.append(f"{doc_id}: missing path")
            elif path in paths:
                errors.append(f"{doc_id}: duplicate path also used by {paths[path]}")
            else:
                paths[path] = doc_id
            for related in document.get("relatedDocuments", []):
                if related not in self.documents:
                    errors.append(f"{doc_id}: unknown related document {related}")
        return errors

    def ignore_patterns(self) -> list[str]:
        return [*DEFAULT_IGNORE, *self.settings.get("ignorePatterns", [])]

    def is_ignored(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        return any(fnmatch.fnmatch(normalized, pattern) for pattern in self.ignore_patterns())

    def is_relevant_source(self, path: str) -> bool:
        if self.is_ignored(path):
            return False
        pure = Path(path)
        return pure.name in RELEVANT_NAMES or pure.suffix.lower() in RELEVANT_SUFFIXES

    def matching_documents(self, source_path: str) -> set[str]:
        normalized = source_path.replace("\\", "/")
        matched: set[str] = set()
        for doc_id, document in self.documents.items():
            explicit = {item.replace("\\", "/") for item in document.get("sourceHashes", {})}
            patterns = document.get("sourcePatterns", [])
            if normalized in explicit or any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns):
                matched.add(doc_id)
        return matched


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
    return DocumentationMap(path=path, data=data)


def create_empty_map(root: Path) -> DocumentationMap:
    return DocumentationMap(
        path=root / "docs" / "_meta" / "documentation-map.json",
        data={
            "schemaVersion": 1,
            "settings": {"ignorePatterns": [], "auditOnlyPatterns": ["**/test/**", "**/*.spec.ts"]},
            "documents": {},
        },
    )
