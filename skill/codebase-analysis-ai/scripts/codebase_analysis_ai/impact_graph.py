"""Resolve direct and one-level documentation impact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .documentation_map import DocumentationMap


@dataclass(frozen=True)
class Impact:
    direct: tuple[str, ...]
    related: tuple[str, ...]
    unmapped: tuple[str, ...]

    @property
    def all_documents(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.direct) | set(self.related)))


def resolve_impact(documentation_map: DocumentationMap, changed_paths: Iterable[str]) -> Impact:
    direct: set[str] = set()
    unmapped: set[str] = set()
    for path in changed_paths:
        if documentation_map.is_ignored(path):
            continue
        matches = documentation_map.matching_documents(path)
        if matches:
            direct.update(matches)
        elif documentation_map.is_relevant_source(path):
            unmapped.add(path)

    related: set[str] = set()
    for doc_id in direct:
        related.update(documentation_map.documents[doc_id].get("relatedDocuments", []))
    related.difference_update(direct)

    return Impact(tuple(sorted(direct)), tuple(sorted(related)), tuple(sorted(unmapped)))
