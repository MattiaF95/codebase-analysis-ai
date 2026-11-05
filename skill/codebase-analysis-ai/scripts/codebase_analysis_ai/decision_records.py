"""Validate decision records without modifying their prose or source hashes."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from .document_kinds import document_kind
from .documentation_map import (
    DECISION_DIRECTORY,
    DOCUMENTATION_INDEX,
    LEGACY_DECISION_DIRECTORY,
    DocumentationMap,
    MapError,
    normalize_repository_path,
)
from .link_validator import repository_links, validate_links


ADR_FILENAME = re.compile(r"^ADR-(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
ADR_TITLE = re.compile(r"^#\s+ADR-(\d{4}):\s+\S")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADR_STATUSES = {"proposed", "accepted", "rejected", "superseded", "deprecated"}


def _normalized_path(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.replace("\\", "/")


def _is_adr_location(path: str) -> bool:
    return path.startswith(DECISION_DIRECTORY) or path.startswith(LEGACY_DECISION_DIRECTORY)


def _index_candidates(path: str) -> list[str]:
    if path.startswith(LEGACY_DECISION_DIRECTORY):
        return [LEGACY_DECISION_DIRECTORY + "index.md", DECISION_DIRECTORY + "index.md"]
    return [DECISION_DIRECTORY + "index.md"]


def _reference_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def _record_number(record: dict[str, Any]) -> str:
    return str(record["number"])


def decision_record_paths(documentation_map: DocumentationMap) -> set[str]:
    """Return every registered path that represents a decision record."""
    paths: set[str] = set()
    for document in documentation_map.documents.values():
        if not isinstance(document, dict):
            continue
        path = _normalized_path(document.get("path"))
        if not path:
            continue
        name = path.rsplit("/", 1)[-1]
        if document.get("documentKind") == "decision-record" or (
            _is_adr_location(path) and ADR_FILENAME.match(name)
        ):
            paths.add(path)
    return paths


def _first_level_one_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line
    return None


def _resolve_reference(value: str, references: dict[str, list[str]]) -> tuple[str | None, str | None]:
    key = value.strip()
    if not key:
        return None, "empty reference"
    matches = references.get(key)
    if not matches:
        number = key.removeprefix("ADR-")
        if number.isdigit():
            number = number.zfill(4)
            matches = references.get(number) or references.get(f"ADR-{number}")
    if not matches:
        return None, f"unknown decision record {value!r}"
    unique = sorted(set(matches))
    if len(unique) > 1:
        return None, f"ambiguous decision record {value!r} matches {', '.join(unique)}"
    return unique[0], None


def validate_decision_records(root: Path, documentation_map: DocumentationMap) -> list[str]:
    """Validate registered decision records and their supersession chains."""
    errors: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    legacy_errors: list[str] = []

    for doc_id, document in documentation_map.documents.items():
        if not isinstance(document, dict):
            continue
        path = _normalized_path(document.get("path"))
        if not path:
            continue
        kind_id = document.get("documentKind")
        name = path.rsplit("/", 1)[-1]
        match = ADR_FILENAME.match(name)
        if kind_id != "decision-record" and not (_is_adr_location(path) and match):
            continue
        if not match:
            target = errors if kind_id == "decision-record" else legacy_errors
            target.append(f"{path}: decision record filename must match ADR-NNNN-<slug>.md")
            continue
        records[doc_id] = {
            "id": doc_id,
            "path": path,
            "number": match.group(1),
            "slug": match.group(2),
            "kind": kind_id == "decision-record",
            "metadata": document.get("metadata") if isinstance(document.get("metadata"), dict) else {},
        }

    if legacy_errors:
        # Legacy path-only decision records are reported by audit, not failed by check.
        errors.extend(legacy_errors)

    numbers: dict[str, str] = {}
    references: dict[str, list[str]] = {}
    for doc_id, record in records.items():
        number = _record_number(record)
        if number in numbers:
            errors.append(f"Duplicate ADR number {number}: {numbers[number]} and {doc_id}")
        else:
            numbers[number] = doc_id
        path = str(record["path"])
        for key in (
            doc_id,
            path,
            path.rsplit("/", 1)[-1],
            number,
            f"ADR-{number}",
        ):
            references.setdefault(key, []).append(doc_id)

    for doc_id, record in records.items():
        if not record["kind"]:
            continue
        path = str(record["path"])
        document = documentation_map.documents[doc_id]
        metadata = record["metadata"]
        raw_metadata = document.get("metadata")
        if raw_metadata is not None and not isinstance(raw_metadata, dict):
            errors.append(f"{path}: decision record metadata must be an object")
        for key in ("supersedes", "relatedPlans"):
            value = metadata.get(key)
            if value is not None and not (
                isinstance(value, str)
                or (isinstance(value, list) and all(isinstance(item, str) for item in value))
            ):
                errors.append(f"{path}: metadata.{key} must be a string or string array")

        status = metadata.get("status")
        if status not in ADR_STATUSES:
            errors.append(
                f"{path}: decision record status must be one of "
                + ", ".join(sorted(ADR_STATUSES))
            )
        recorded_date = metadata.get("date")
        if not isinstance(recorded_date, str) or not ISO_DATE.fullmatch(recorded_date):
            errors.append(f"{path}: decision record date must use YYYY-MM-DD")
        else:
            try:
                date.fromisoformat(recorded_date)
            except ValueError:
                errors.append(f"{path}: decision record date is not a valid calendar date")

        catalog = document_kind("decision-record")
        assert catalog is not None
        sections = document.get("sections")
        if not isinstance(sections, dict):
            errors.append(f"{path}: decision record must declare localized sections")
        else:
            missing = [key for key in catalog.required_sections if key not in sections]
            if missing:
                errors.append(
                    f"{path}: decision record is missing sections: " + ", ".join(missing)
                )

        if document.get("sourcePatterns"):
            errors.append(f"{path}: decision records must not declare sourcePatterns")
        if document.get("sourceHashes"):
            errors.append(f"{path}: decision records must not record sourceHashes")

        document_file = root / path
        if document_file.is_file():
            heading = _first_level_one_heading(document_file.read_text(encoding="utf-8"))
            match = ADR_TITLE.match(heading or "")
            if match is None:
                errors.append(f"{path}: decision record title must start with ADR-<number>:")
            elif match.group(1) != record["number"]:
                errors.append(
                    f"{path}: title number ADR-{match.group(1)} does not match filename ADR-{record['number']}"
                )

        index_path = next(
            (candidate for candidate in _index_candidates(path) if (root / candidate).is_file()),
            None,
        )
        if index_path is None:
            errors.append(f"{path}: missing decision index {_index_candidates(path)[0]}")
        else:
            links = repository_links(root, index_path)
            if path not in links:
                errors.append(f"{path}: decision index {index_path} does not link this record")
            if (root / DOCUMENTATION_INDEX).is_file():
                index_links = repository_links(root, DOCUMENTATION_INDEX)
                if index_path not in index_links:
                    errors.append(
                        f"{DOCUMENTATION_INDEX}: documentation index does not link {index_path}"
                    )

        supersedes = _reference_list(metadata.get("supersedes"))
        superseded_by = metadata.get("supersededBy")
        if superseded_by is not None and not isinstance(superseded_by, str):
            errors.append(f"{path}: metadata.supersededBy must be a string")
            superseded_by = None
        resolved_superseded_by: str | None = None
        if isinstance(superseded_by, str) and superseded_by:
            resolved_superseded_by, issue = _resolve_reference(superseded_by, references)
            if issue:
                errors.append(f"{path}: supersededBy {issue}")

        if status != "superseded" and superseded_by:
            errors.append(f"{path}: supersededBy is only allowed when status is superseded")
        if status == "superseded" and not superseded_by:
            errors.append(f"{path}: status superseded requires metadata.supersededBy")

        for value in supersedes:
            target_id, issue = _resolve_reference(value, references)
            if issue:
                errors.append(f"{path}: supersedes {issue}")
                continue
            target = records[target_id] if target_id is not None else None
            if target is None:
                continue
            target_status = target["metadata"].get("status")
            if status == "accepted" and target_status != "superseded":
                errors.append(
                    f"{path}: supersedes {value} but {target['path']} is not marked superseded"
                )
            if target_status == "superseded":
                target_back = target["metadata"].get("supersededBy")
                resolved_back, _ = (
                    _resolve_reference(target_back, references)
                    if isinstance(target_back, str) and target_back
                    else (None, None)
                )
                if resolved_back != doc_id:
                    errors.append(
                        f"{target['path']}: superseded record does not declare supersededBy pointing to {doc_id}"
                    )

        if resolved_superseded_by is not None:
            target = records[resolved_superseded_by]
            target_supersedes = _reference_list(target["metadata"].get("supersedes"))
            target_status = target["metadata"].get("status")
            if target_status not in {"accepted", "proposed"}:
                errors.append(
                    f"{path}: supersededBy target {target['path']} must be accepted or proposed"
                )
            if not any(
                _resolve_reference(value, references)[0] == doc_id
                for value in target_supersedes
            ):
                errors.append(
                    f"{path}: supersededBy target {target['path']} does not declare this record in supersedes"
                )

        if status == "accepted" and resolved_superseded_by is not None:
            errors.append(f"{path}: an accepted record cannot itself be supersededBy another record")

        related_plans = _reference_list(metadata.get("relatedPlans"))
        for plan in related_plans:
            try:
                normalized = normalize_repository_path(plan)
            except MapError as exc:
                errors.append(f"{path}: relatedPlans: {exc}")
                continue
            if not (root / normalized).is_file():
                errors.append(f"{path}: related plan not found: {normalized}")

    adr_paths = sorted(str(record["path"]) for record in records.values() if record["kind"])
    errors.extend(validate_links(root, adr_paths))
    return errors
