"""Find evidence-backed TODO and FIXME markers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


MARKER = re.compile(r"\b(TODO|FIXME|XXX)\b[:\s-]*(.*)", re.IGNORECASE)


def scan_todos(root: Path, paths: Iterable[str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for relative in sorted(set(paths)):
        path = root / relative
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            match = MARKER.search(line)
            if match:
                findings.append({"path": relative, "line": number, "marker": match.group(1).upper(), "text": match.group(2).strip()})
    return findings

