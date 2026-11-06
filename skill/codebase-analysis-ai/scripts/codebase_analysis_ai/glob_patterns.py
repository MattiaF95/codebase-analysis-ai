"""Small, dependency-free glob engine shared by map configuration.

The engine intentionally implements a documented subset of glob syntax:

* ``*`` matches zero or more characters except ``/``.
* ``?`` matches exactly one character except ``/``.
* ``**`` matches zero or more characters including ``/``.
* ``**/`` matches zero or more directories, so it also matches zero
  directories (``**/test/**`` matches both ``test/a.py`` and
  ``src/test/a.py``).

Maps that do not declare any ``documentKind`` are legacy maps. They keep the
historical ``fnmatch`` semantics (``*`` also crosses ``/``) through
``legacy_glob_match`` so existing ``sourcePatterns`` and ``ignorePatterns``
continue to match the same files.

Character classes (``[...]``) are not supported; every other character is
matched literally. Matching is performed on the whole normalized path and is
case-sensitive, which keeps the semantics identical across platforms.
"""

from __future__ import annotations

import fnmatch
import re
from functools import lru_cache
from typing import Pattern


def _translate(pattern: str) -> str:
    translated: list[str] = []
    index = 0
    length = len(pattern)
    while index < length:
        character = pattern[index]
        if character == "*":
            if index + 1 < length and pattern[index + 1] == "*":
                if index + 2 < length and pattern[index + 2] == "/":
                    translated.append("(?:.*/)?")
                    index += 3
                else:
                    translated.append(".*")
                    index += 2
            else:
                translated.append("[^/]*")
                index += 1
        elif character == "?":
            translated.append("[^/]")
            index += 1
        else:
            translated.append(re.escape(character))
            index += 1
    return "^" + "".join(translated) + "$"


@lru_cache(maxsize=None)
def compile_glob(pattern: str) -> Pattern[str]:
    """Compile one repository glob pattern into a case-sensitive regex."""
    return re.compile(_translate(pattern.replace("\\", "/")))


def glob_match(path: str, pattern: str) -> bool:
    """Return whether a normalized repository path matches a glob pattern."""
    return compile_glob(pattern).match(path.replace("\\", "/")) is not None


def legacy_glob_match(path: str, pattern: str) -> bool:
    """Match with the historical ``fnmatch`` semantics used by legacy maps."""
    return fnmatch.fnmatch(path.replace("\\", "/"), pattern.replace("\\", "/"))
