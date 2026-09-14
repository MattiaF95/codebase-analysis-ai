"""Find evidence-backed TODO and FIXME markers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .documentation_map import normalize_repository_path, resolve_repository_path


MARKER = re.compile(r"\b(TODO|FIXME|XXX)\b[:\s-]*(.*)", re.IGNORECASE)
ACTIONABLE_START = re.compile(
    r"^\s*(?:(?:[-*+]|\d+[.)])\s+)?(?:TODO|FIXME|XXX)\b",
    re.IGNORECASE,
)
COMMENT_MARKER = re.compile(
    r"(?:^|\s)(?:#|//|/\*+|<!--|--|;)\s*(?:TODO|FIXME|XXX)\b",
    re.IGNORECASE,
)


def _is_actionable_marker(line: str, match: re.Match[str]) -> bool:
    """Keep markers that look like work items, not prose mentioning the words."""
    if ACTIONABLE_START.search(line):
        return True
    return bool(COMMENT_MARKER.search(line[:match.end()]))


def scan_todos(root: Path, paths: Iterable[str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for relative in sorted({normalize_repository_path(path) for path in paths}):
        path = resolve_repository_path(root, relative)
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            match = MARKER.search(line)
            if match and _is_actionable_marker(line, match):
                findings.append({"path": relative, "line": number, "marker": match.group(1).upper(), "text": match.group(2).strip()})
    return findings
