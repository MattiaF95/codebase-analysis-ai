"""Validate relative Markdown links."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def validate_links(root: Path, markdown_paths: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for relative in sorted(set(markdown_paths)):
        document = root / relative
        if not document.is_file():
            errors.append(f"Missing document: {relative}")
            continue
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{relative}: link escapes repository: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{relative}: broken link: {raw_target}")
    return errors

