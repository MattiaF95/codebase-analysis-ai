"""Optional detection and link validation for PlanVault execution plans.

PlanVault is never required. This module only recognizes plans that already
exist in the repository and validates links that explicitly point at decision
records. It never writes, moves, or rewrites a plan.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .documentation_map import (
    DECISION_DIRECTORY,
    LEGACY_DECISION_DIRECTORY,
    DocumentationMap,
    MapError,
    normalize_repository_path,
)
from .link_validator import resolved_link_targets


PLANS_DIRECTORY = "plans"
CORE_FILES = ("spec.md", "plan.md", "tasks.md")
ADR_PATH = re.compile(
    "^(?:" + re.escape(DECISION_DIRECTORY) + "|" + re.escape(LEGACY_DECISION_DIRECTORY) + r")ADR-\d{4}-[a-z0-9-]+\.md$"
)
IGNORED_DIRECTORIES = {".git", "_archive", "__pycache__", "node_modules"}


def detect_planvault_plans(root: Path) -> list[dict[str, Any]]:
    """Return recognized PlanVault artifacts without requiring the skill."""
    plans_root = root / PLANS_DIRECTORY
    if not plans_root.is_dir():
        return []

    artifacts: list[dict[str, Any]] = []
    three_core_directories: set[str] = set()
    markdown_files: list[Path] = []
    for current, directories, filenames in os.walk(plans_root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in IGNORED_DIRECTORIES)
        markdown_files.extend(
            Path(current) / name for name in sorted(filenames) if name.endswith(".md")
        )
        if all(core in filenames for core in CORE_FILES):
            directory = Path(current)
            relative_directory = directory.relative_to(root).as_posix()
            three_core_directories.add(relative_directory)
            artifacts.append({
                "kind": "three-core",
                "directory": relative_directory,
                "files": [
                    (directory / core).relative_to(root).as_posix()
                    for core in CORE_FILES
                ],
            })

    for candidate in markdown_files:
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(root).as_posix()
        parent = candidate.parent.relative_to(root).as_posix()
        if parent in three_core_directories:
            continue
        artifacts.append({"kind": "single-file", "directory": parent, "files": [relative]})

    return sorted(artifacts, key=lambda item: (item["kind"], item["directory"], item["files"]))


def _decision_records(documentation_map: DocumentationMap) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for doc_id, document in documentation_map.documents.items():
        if not isinstance(document, dict):
            continue
        path = document.get("path")
        if not isinstance(path, str) or not path:
            continue
        normalized = path.replace("\\", "/")
        # Legacy path-only records in docs/adr/ are registered decision records too.
        if document.get("documentKind") != "decision-record" and not ADR_PATH.match(normalized):
            continue
        metadata = document.get("metadata")
        records[normalized] = {
            "id": doc_id,
            "path": normalized,
            "metadata": metadata if isinstance(metadata, dict) else {},
        }
    return records


def _related_plans(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("relatedPlans")
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def validate_planvault_links(root: Path, documentation_map: DocumentationMap) -> list[str]:
    """Validate explicit plan-to-ADR links and their reverse metadata.

    Missing PlanVault plans, unknown link shapes, and repositories without
    PlanVault produce no error. Only links that already target a decision-record
    path are inspected.
    """
    errors: list[str] = []
    artifacts = detect_planvault_plans(root)
    if not artifacts:
        return errors
    records = _decision_records(documentation_map)
    root = root.resolve()

    for artifact in artifacts:
        for plan_path in artifact["files"]:
            for target in sorted(resolved_link_targets(root, plan_path)):
                if not ADR_PATH.match(target):
                    continue
                if not (root / target).is_file():
                    errors.append(f"{plan_path}: broken link to decision record: {target}")
                    continue
                record = records.get(target)
                if record is None:
                    errors.append(
                        f"{plan_path}: linked decision record is not registered: {target}"
                    )
                    continue
                related = set()
                for value in _related_plans(record["metadata"]):
                    try:
                        related.add(normalize_repository_path(value))
                    except MapError:
                        continue
                # A three-core plan is one unit: listing any of its files suffices.
                if not related.intersection(artifact["files"]):
                    errors.append(
                        f"{plan_path}: decision record {target} does not list this plan in metadata.relatedPlans"
                    )
    return errors
