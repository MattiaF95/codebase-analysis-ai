"""Hash repository source files without exposing their contents."""

from __future__ import annotations

import hashlib
from pathlib import Path


DELETED = "<deleted>"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return DELETED
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

