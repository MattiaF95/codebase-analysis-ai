"""Validate stable machine-readable contracts in generated Markdown documents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


SCOPE_START = "<!-- codebase-analysis-ai:scope:start -->"
SCOPE_END = "<!-- codebase-analysis-ai:scope:end -->"
FINDING_PREFIX = "<!-- codebase-analysis-ai:finding "
FINDING_SUFFIX = " -->"
FINDING_KINDS = {"bug", "security", "reliability", "maintainability", "coverage-gap", "documentation"}
FINDING_SEVERITIES = {"critical", "high", "medium", "low", "info"}
FINDING_VERIFICATIONS = {"source-only", "test", "runtime", "external-state"}


def _repository_relative_path(root: Path, requested: str) -> tuple[str, Path | None, str | None]:
    normalized = requested.replace("\\", "/")
    document = (root / normalized).resolve()
    try:
        relative = document.relative_to(root).as_posix()
    except ValueError:
        return normalized, None, f"{normalized}: path escapes repository"
    return relative, document, None


def _sentences(text: str) -> int:
    return len([part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()])


def _scope_issues(relative: str, text: str) -> list[str]:
    starts = text.count(SCOPE_START)
    ends = text.count(SCOPE_END)
    if starts == 0 and ends == 0:
        return [f"{relative}: missing managed scope markers"]
    if starts != 1 or ends != 1 or text.index(SCOPE_START) > text.index(SCOPE_END):
        return [f"{relative}: scope markers must form exactly one ordered pair"]
    scope = text.split(SCOPE_START, 1)[1].split(SCOPE_END, 1)[0].strip()
    issues: list[str] = []
    if not scope:
        issues.append(f"{relative}: managed scope is empty")
    if len(scope.split()) > 35:
        issues.append(f"{relative}: managed scope exceeds 35 words")
    if _sentences(scope) > 2:
        issues.append(f"{relative}: managed scope exceeds two sentences")
    return issues


def _finding_issues(relative: str, text: str) -> list[str]:
    issues: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if "<!-- codebase-analysis-ai:finding" not in stripped:
            continue
        if not stripped.startswith(FINDING_PREFIX) or not stripped.endswith(FINDING_SUFFIX):
            issues.append(f"{relative}:{line_number}: malformed finding metadata marker")
            continue
        raw = stripped[len(FINDING_PREFIX):-len(FINDING_SUFFIX)]
        try:
            finding = json.loads(raw)
        except json.JSONDecodeError as exc:
            issues.append(f"{relative}:{line_number}: invalid finding metadata JSON: {exc.msg}")
            continue
        if not isinstance(finding, dict):
            issues.append(f"{relative}:{line_number}: finding metadata must be an object")
            continue
        if finding.get("kind") not in FINDING_KINDS:
            issues.append(f"{relative}:{line_number}: unsupported finding kind")
        if finding.get("severity") not in FINDING_SEVERITIES:
            issues.append(f"{relative}:{line_number}: unsupported finding severity")
        if finding.get("verification") not in FINDING_VERIFICATIONS:
            issues.append(f"{relative}:{line_number}: unsupported finding verification")
    return issues


def validate_documents(root: Path, markdown_paths: Iterable[str] | None = None) -> dict[str, object]:
    root = root.resolve()
    if markdown_paths:
        paths = sorted(set(path.replace("\\", "/") for path in markdown_paths))
    else:
        paths = sorted(
            path.relative_to(root).as_posix()
            for path in (root / "docs").rglob("*.md")
            if "_archive" not in path.relative_to(root / "docs").parts
        ) if (root / "docs").is_dir() else []
    issues: list[str] = []
    inspected: list[str] = []
    for requested in paths:
        relative, document, path_issue = _repository_relative_path(root, requested)
        if path_issue:
            issues.append(path_issue)
            continue
        assert document is not None
        if not document.is_file():
            issues.append(f"Missing document: {relative}")
            continue
        inspected.append(relative)
        text = document.read_text(encoding="utf-8")
        issues.extend(_scope_issues(relative, text))
        issues.extend(_finding_issues(relative, text))
    return {"documents": inspected, "issues": issues, "valid": not issues}
