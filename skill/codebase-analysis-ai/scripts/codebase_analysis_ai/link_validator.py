"""Validate repository-relative Markdown links without interpreting code examples."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit


REFERENCE_DEFINITION = re.compile(r"(?m)^[ ]{0,3}\[([^\]]+)\]:[ \t]*(<[^>]*>|\S+).*$")


def _reference_id(value: str) -> str:
    return " ".join(value.split()).casefold()


def _mask_code(text: str) -> str:
    output = list(text)
    fence: tuple[str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^[ ]{0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = (marker[0], len(marker))
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            for index in range(offset, offset + len(line)):
                if output[index] not in "\r\n":
                    output[index] = " "
        elif fence is not None:
            for index in range(offset, offset + len(line)):
                if output[index] not in "\r\n":
                    output[index] = " "
        offset += len(line)

    masked = "".join(output)
    output = list(masked)
    index = 0
    while index < len(masked):
        if masked[index] != "`":
            index += 1
            continue
        end_ticks = index
        while end_ticks < len(masked) and masked[end_ticks] == "`":
            end_ticks += 1
        marker = masked[index:end_ticks]
        closing = masked.find(marker, end_ticks)
        if closing < 0:
            index = end_ticks
            continue
        for position in range(index, closing + len(marker)):
            if output[position] not in "\r\n":
                output[position] = " "
        index = closing + len(marker)
    return "".join(output)


def _closing_bracket(text: str, start: int) -> int | None:
    depth = 1
    index = start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _inline_target(text: str, opening: int) -> tuple[str, int] | None:
    index = opening + 1
    while index < len(text) and text[index].isspace():
        index += 1
    if index < len(text) and text[index] == "<":
        closing = text.find(">", index + 1)
        if closing < 0:
            return None
        target = text[index:closing + 1]
        index = closing + 1
    else:
        start = index
        depth = 0
        while index < len(text):
            character = text[index]
            if character == "\\":
                index += 2
                continue
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    break
                depth -= 1
            elif character.isspace() and depth == 0:
                break
            index += 1
        target = text[start:index]
    closing = index
    nested = 0
    while closing < len(text):
        character = text[closing]
        if character == "\\":
            closing += 2
            continue
        if character == "(":
            nested += 1
        elif character == ")":
            if nested == 0:
                return target, closing
            nested -= 1
        closing += 1
    return None


def _targets(text: str) -> list[str]:
    masked = _mask_code(text)
    references: dict[str, str] = {}
    definition_spans: list[tuple[int, int]] = []
    for match in REFERENCE_DEFINITION.finditer(masked):
        references[_reference_id(match.group(1))] = match.group(2)
        definition_spans.append(match.span())
    if definition_spans:
        characters = list(masked)
        for start, end in definition_spans:
            characters[start:end] = [" " if char not in "\r\n" else char for char in characters[start:end]]
        masked = "".join(characters)

    targets: list[str] = []
    index = 0
    while index < len(masked):
        if masked[index] != "[" or (index > 0 and masked[index - 1] in {"!", "\\"}):
            index += 1
            continue
        label_end = _closing_bracket(masked, index)
        if label_end is None:
            index += 1
            continue
        label = masked[index + 1:label_end]
        next_index = label_end + 1
        if next_index < len(masked) and masked[next_index] == "(":
            parsed = _inline_target(masked, next_index)
            if parsed is not None:
                target, end = parsed
                targets.append(target)
                index = end + 1
                continue
        reference_id = label
        if next_index < len(masked) and masked[next_index] == "[":
            reference_end = _closing_bracket(masked, next_index)
            if reference_end is not None:
                reference_id = masked[next_index + 1:reference_end] or label
                next_index = reference_end + 1
        target = references.get(_reference_id(reference_id))
        if target is not None:
            targets.append(target)
        index = next_index
    return targets


def _destination(raw_target: str) -> str:
    target = raw_target.strip().strip("<>")
    target = re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", target)
    return unquote(target.split("#", 1)[0])


def validate_links(root: Path, markdown_paths: Iterable[str]) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    for relative in sorted(set(markdown_paths)):
        document = root / relative
        if not document.is_file():
            errors.append(f"Missing document: {relative}")
            continue
        text = document.read_text(encoding="utf-8")
        for raw_target in _targets(text):
            stripped = raw_target.strip().strip("<>")
            if not stripped or stripped.startswith(("#", "//")) or urlsplit(stripped).scheme:
                continue
            target = _destination(raw_target)
            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{relative}: link escapes repository: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{relative}: broken link: {raw_target}")
    return errors
