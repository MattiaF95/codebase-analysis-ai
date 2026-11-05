"""Single runtime catalog of documentation kinds and their section contracts.

The catalog is the only machine-readable source of truth for document kinds.
Human documentation in ``references/document-style.md`` and
``references/documentation-schema.md`` must stay aligned with this module
without duplicating the values as a second catalog.

Section identifiers are stable, language-neutral keys. A documentation map
stores, for each document, a ``sections`` object that maps those keys to the
localized second-level headings actually used in the file. Validation therefore
works with the project language instead of assuming English headings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentKind:
    """Contract for one documentation kind."""

    id: str
    required_sections: tuple[str, ...]
    recommended_sections: tuple[str, ...] = ()
    lifecycle: str = "living"
    index_policy: str = "indexed"
    default_location: str = ""
    source_patterns_required: bool = True


# Canonical English labels used only as authoring guidance. A map may declare
# localized labels for every key; validation never requires these exact words.
SECTION_LABELS = {
    "coverage": "What this document covers",
    "status": "Project status",
    "quickStart": "Quick start",
    "activeFunctionality": "Active functionality",
    "architecture": "Architecture overview",
    "technologies": "Technologies and dependencies",
    "structure": "Repository structure",
    "configuration": "Configuration",
    "tests": "Tests",
    "plannedWork": "Planned work and TODOs",
    "documentation": "Documentation",
    "license": "License",
    "problems": "Detected problems",
    "limitations": "Known limitations",
    "gettingStarted": "Getting started",
    "areas": "Documentation areas",
    "flows": "Main flows",
    "indexStatus": "Documentation status",
    "documents": "Documents",
    "context": "Context",
    "contents": "What this area contains",
    "entryPoints": "Main entry points",
    "internalStructure": "Internal structure",
    "relatedDocumentation": "Related documentation",
    "sources": "Sources",
    "responsibilities": "Responsibilities",
    "howItWorks": "How it works",
    "implementation": "Implementation details",
    "components": "Components",
    "boundaries": "Boundaries",
    "decisions": "Decisions",
    "endpoints": "Endpoints",
    "authentication": "Authentication and authorization",
    "errors": "Errors",
    "examples": "Examples",
    "versioning": "Versioning",
    "entities": "Entities",
    "relationships": "Relationships",
    "storage": "Storage",
    "migrations": "Migrations",
    "symptoms": "Symptoms",
    "prerequisites": "Prerequisites",
    "procedure": "Procedure",
    "verification": "Verification",
    "rollback": "Rollback",
    "escalation": "Escalation",
    "levels": "Test levels",
    "environments": "Environments",
    "coverageGaps": "Coverage gaps",
    "gates": "Quality gates",
    "priorities": "Priorities",
    "items": "Items",
    "acceptedRisks": "Accepted risks",
    "decision": "Decision",
    "alternatives": "Alternatives considered",
    "consequences": "Consequences",
    "evidence": "Evidence",
    "links": "Links",
    "reference": "Reference",
    "method": "Method",
    "findings": "Findings",
    "recommendations": "Recommendations",
}

LIFECYCLES = {"living", "immutable-after-acceptance", "snapshot"}
INDEX_POLICIES = {"indexed", "kind-index", "excluded"}


DOCUMENT_KINDS: dict[str, DocumentKind] = {
    "project-readme": DocumentKind(
        id="project-readme",
        required_sections=(
            "coverage", "status", "quickStart", "activeFunctionality",
            "architecture", "technologies", "structure", "configuration",
            "tests", "plannedWork", "documentation", "license",
        ),
        recommended_sections=("problems", "limitations"),
        lifecycle="living",
        index_policy="indexed",
        default_location="README.md",
        source_patterns_required=False,
    ),
    "documentation-index": DocumentKind(
        id="documentation-index",
        required_sections=("coverage", "gettingStarted", "areas", "flows", "indexStatus"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/index.md",
        source_patterns_required=False,
    ),
    "area": DocumentKind(
        id="area",
        required_sections=(
            "coverage", "context", "contents", "entryPoints", "internalStructure",
            "technologies", "activeFunctionality", "relatedDocumentation", "sources",
        ),
        recommended_sections=("problems", "plannedWork"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/<area>/README.md",
    ),
    "topic": DocumentKind(
        id="topic",
        required_sections=(
            "coverage", "context", "responsibilities", "howItWorks",
            "activeFunctionality", "relatedDocumentation", "sources",
        ),
        recommended_sections=("technologies", "implementation", "problems", "plannedWork"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/<area>/<topic>.md",
    ),
    "architecture": DocumentKind(
        id="architecture",
        required_sections=("coverage", "context", "components", "flows", "boundaries", "decisions", "sources"),
        recommended_sections=("problems", "relatedDocumentation"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/architecture/",
    ),
    "api-reference": DocumentKind(
        id="api-reference",
        required_sections=(
            "coverage", "context", "endpoints", "authentication", "errors", "examples", "sources",
        ),
        recommended_sections=("versioning",),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/reference/",
    ),
    "data-model": DocumentKind(
        id="data-model",
        required_sections=("coverage", "context", "entities", "relationships", "storage", "migrations", "sources"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/<area>/data-model.md",
    ),
    "runbook": DocumentKind(
        id="runbook",
        required_sections=(
            "coverage", "context", "symptoms", "prerequisites", "procedure",
            "verification", "rollback", "escalation", "sources",
        ),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/runbooks/",
    ),
    "test-strategy": DocumentKind(
        id="test-strategy",
        required_sections=("coverage", "context", "levels", "environments", "coverageGaps", "gates", "sources"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/test-strategy.md",
    ),
    "backlog": DocumentKind(
        id="backlog",
        required_sections=("coverage", "context", "priorities", "items", "acceptedRisks", "sources"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/backlog.md",
    ),
    "kind-index": DocumentKind(
        id="kind-index",
        required_sections=("coverage", "relatedDocumentation"),
        recommended_sections=("documents",),
        lifecycle="living",
        index_policy="kind-index",
        default_location="docs/<kind>/index.md",
        source_patterns_required=False,
    ),
    "decision-record": DocumentKind(
        id="decision-record",
        required_sections=("context", "decision", "alternatives", "consequences", "evidence", "links"),
        lifecycle="immutable-after-acceptance",
        index_policy="kind-index",
        default_location="docs/decisions/",
        source_patterns_required=False,
    ),
    "reference": DocumentKind(
        id="reference",
        required_sections=("coverage", "context", "reference", "relatedDocumentation", "sources"),
        recommended_sections=("howItWorks", "examples"),
        lifecycle="living",
        index_policy="indexed",
        default_location="docs/reference/",
    ),
    "analysis-report": DocumentKind(
        id="analysis-report",
        required_sections=("coverage", "method", "evidence", "findings", "recommendations"),
        lifecycle="snapshot",
        index_policy="excluded",
        default_location="docs/_analysis/",
        source_patterns_required=False,
    ),
}


def document_kind(kind_id: object) -> DocumentKind | None:
    """Return the catalog entry for a kind identifier, or ``None``."""
    if not isinstance(kind_id, str):
        return None
    return DOCUMENT_KINDS.get(kind_id)


def known_kind_ids() -> tuple[str, ...]:
    """Return every supported document kind in stable catalog order."""
    return tuple(DOCUMENT_KINDS)


def known_section_keys() -> frozenset[str]:
    """Return every section key understood by the catalog."""
    return frozenset(SECTION_LABELS)


def is_known_section(key: object) -> bool:
    return isinstance(key, str) and key in SECTION_LABELS


def section_contract_errors(kind_id: object, sections: object) -> list[str]:
    """Validate a ``sections`` declaration against its document kind.

    ``sections`` is expected to be a mapping of canonical section keys to the
    localized second-level heading labels used by the document. Structural
    errors are reported here; heading presence is checked against the file by
    the document validator.
    """
    errors: list[str] = []
    kind = document_kind(kind_id)
    if kind is None:
        return errors
    if sections is None:
        return errors
    if not isinstance(sections, dict):
        return ["sections must be an object mapping section keys to headings"]
    labels: dict[str, str] = {}
    for key, label in sections.items():
        if not isinstance(key, str) or not key:
            errors.append("sections keys must be non-empty strings")
            continue
        if key not in SECTION_LABELS:
            errors.append(f"unknown section key {key!r}")
            continue
        if not isinstance(label, str) or not label.strip():
            errors.append(f"sections.{key} must be a non-empty heading label")
            continue
        normalized = " ".join(label.split())
        if normalized in labels:
            errors.append(
                f"sections.{key} duplicates the heading label used by sections.{labels[normalized]}"
            )
        else:
            labels[normalized] = key
    missing = [key for key in kind.required_sections if key not in sections]
    if missing:
        errors.append("missing required sections for " + kind.id + ": " + ", ".join(missing))
    return errors
