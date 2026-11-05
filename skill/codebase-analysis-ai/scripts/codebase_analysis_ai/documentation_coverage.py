"""Compute documentation coverage and validate index navigation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .document_kinds import document_kind, known_kind_ids
from .documentation_map import (
    DOCUMENTATION_INDEX,
    DocumentationMap,
    active_document_paths,
)
from .link_validator import repository_links


COVERAGE_PATH = "docs/_meta/coverage.md"
ADR_STATUS_ORDER = ("proposed", "accepted", "rejected", "superseded", "deprecated", "unknown")


def _index_document(documentation_map: DocumentationMap) -> dict[str, Any] | None:
    for document in documentation_map.documents.values():
        if not isinstance(document, dict):
            continue
        if document.get("path") == DOCUMENTATION_INDEX:
            return document
    return None


def coverage_counts(documentation_map: DocumentationMap) -> dict[str, Any]:
    """Return deterministic document and decision-record counts."""
    kinds: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    policies: Counter[str] = Counter()
    for document in documentation_map.documents.values():
        if not isinstance(document, dict):
            continue
        kind_id = document.get("documentKind")
        kind = document_kind(kind_id)
        if kind is None:
            kinds["legacy"] += 1
            policies["legacy"] += 1
        else:
            kinds[kind.id] += 1
            policies[kind.index_policy] += 1
        if kind is not None and kind.id == "decision-record":
            metadata = document.get("metadata")
            status = metadata.get("status") if isinstance(metadata, dict) else None
            if not isinstance(status, str) or not status:
                status = "unknown"
            statuses[status] += 1

    ordered_kinds = {
        kind_id: kinds[kind_id]
        for kind_id in known_kind_ids()
        if kinds.get(kind_id)
    }
    if kinds.get("legacy"):
        ordered_kinds["legacy"] = kinds["legacy"]
    ordered_statuses = {
        status: statuses[status]
        for status in ADR_STATUS_ORDER
        if statuses.get(status)
    }
    return {
        "documents": sum(kinds.values()),
        "byKind": ordered_kinds,
        "byAdrStatus": ordered_statuses,
        "byIndexPolicy": dict(sorted(policies.items())),
    }


def coverage_markdown(counts: dict[str, Any]) -> str:
    """Render coverage counts as a portable Markdown document."""
    lines = [
        "# Documentation coverage",
        "",
        "## Documents by kind",
        "",
        "| Kind | Count |",
        "|---|---|",
    ]
    for kind, count in counts.get("byKind", {}).items():
        lines.append(f"| `{kind}` | {count} |")
    lines.extend([
        "",
        "## Decision records by status",
        "",
        "| Status | Count |",
        "|---|---|",
    ])
    statuses = counts.get("byAdrStatus", {})
    if statuses:
        for status, count in statuses.items():
            lines.append(f"| `{status}` | {count} |")
    else:
        lines.append("| none | 0 |")
    lines.extend([
        "",
        "## Index policy",
        "",
        "| Policy | Count |",
        "|---|---|",
    ])
    for policy, count in counts.get("byIndexPolicy", {}).items():
        lines.append(f"| `{policy}` | {count} |")
    return "\n".join(lines) + "\n"


def navigation_issues(root: Path, documentation_map: DocumentationMap) -> dict[str, list[str]]:
    """Validate that the canonical index links active indexes and coverage.

    Navigation is enforced only when ``docs/index.md`` declares the
    ``documentation-index`` kind. Legacy maps therefore keep their previous
    behavior and are reported through audit instead of becoming blocking.
    """
    index = _index_document(documentation_map)
    navigation: list[str] = []
    coverage: list[str] = []
    if index is None or index.get("documentKind") != "documentation-index":
        return {"navigationErrors": navigation, "coverageErrors": coverage}

    root = root.resolve()
    links = repository_links(root, DOCUMENTATION_INDEX)

    for path in active_document_paths(root):
        if path == DOCUMENTATION_INDEX:
            continue
        if path.rsplit("/", 1)[-1] != "index.md":
            continue
        if path not in links:
            navigation.append(f"Documentation index does not link {path}")

    coverage_path = root / COVERAGE_PATH
    if not coverage_path.is_file():
        coverage.append(f"Missing documentation coverage: {COVERAGE_PATH}")
    elif COVERAGE_PATH not in links:
        coverage.append(f"Documentation index does not link {COVERAGE_PATH}")
    return {"navigationErrors": navigation, "coverageErrors": coverage}
