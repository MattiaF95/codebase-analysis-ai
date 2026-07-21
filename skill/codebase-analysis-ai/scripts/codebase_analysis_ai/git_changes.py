"""Collect repository-relative changes from Git."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


ZERO_SHA = "0" * 40


@dataclass(frozen=True)
class Change:
    path: str
    status: str
    old_path: str | None = None


class GitError(RuntimeError):
    pass


def run_git(root: Path, *args: str, check: bool = True) -> str:
    return run_git_bytes(root, *args, check=check).decode("utf-8", errors="surrogateescape")


def run_git_bytes(root: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return result.stdout


def _git_succeeds(root: Path, *args: str) -> bool:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _is_shallow(root: Path) -> bool:
    return run_git(root, "rev-parse", "--is-shallow-repository").strip() == "true"


def _require_object(root: Path, revision: str) -> None:
    if _git_succeeds(root, "cat-file", "-e", f"{revision}^{{commit}}"):
        return
    suffix = "; repository history is shallow" if _is_shallow(root) else ""
    raise GitError(f"required Git revision is unavailable: {revision}{suffix}")


def repository_root(path: Path) -> Path:
    output = run_git(path, "rev-parse", "--show-toplevel")
    return Path(output.strip()).resolve()


def _parse_name_status(output: str) -> list[Change]:
    changes: list[Change] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_code = parts[0]
        status = status_code[0]
        if status in {"R", "C"} and len(parts) >= 3:
            changes.append(Change(path=parts[2], old_path=parts[1], status=status))
        elif len(parts) >= 2:
            changes.append(Change(path=parts[1], status=status))
    return changes


def _decode_path(value: bytes) -> str:
    return os.fsdecode(value)


def _parse_name_status_z(output: bytes) -> list[Change]:
    tokens = output.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    changes: list[Change] = []
    index = 0
    while index < len(tokens):
        status_code = tokens[index].decode("ascii", errors="replace")
        index += 1
        if not status_code:
            raise GitError("Git returned an empty name-status record")
        status = status_code[0]
        required = 2 if status in {"R", "C"} else 1
        if index + required > len(tokens):
            raise GitError(f"Git returned an incomplete name-status record: {status_code}")
        if required == 2:
            old_path = _decode_path(tokens[index])
            path = _decode_path(tokens[index + 1])
            changes.append(Change(path=path, old_path=old_path, status=status))
        else:
            changes.append(Change(path=_decode_path(tokens[index]), status=status))
        index += required
    return changes


def _deduplicate(changes: Iterable[Change]) -> list[Change]:
    merged: dict[str, Change] = {}
    for change in changes:
        merged[change.path] = change
    return sorted(merged.values(), key=lambda item: item.path)


def range_changes(root: Path, base: str | None, head: str = "HEAD") -> list[Change]:
    _require_object(root, head)
    if not base:
        output = run_git_bytes(root, "diff-tree", "--root", "--no-commit-id", "--name-status", "-z", "-r", head)
    else:
        _require_object(root, base)
        output = run_git_bytes(root, "diff", "--name-status", "-z", "--find-renames", base, head)
    return _parse_name_status_z(output)


def _changes_for_commits(root: Path, commits: Iterable[str]) -> list[Change]:
    changes: list[Change] = []
    for commit in commits:
        output = run_git_bytes(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-status",
            "-z",
            "--find-renames",
            "-r",
            commit,
        )
        changes.extend(_parse_name_status_z(output))
    return _deduplicate(changes)


def new_ref_changes(root: Path, head: str) -> list[Change]:
    """Collect every commit introduced by a ref that does not yet exist remotely."""
    _require_object(root, head)
    if _is_shallow(root):
        raise GitError("cannot validate a new ref with incomplete shallow history")
    commits = run_git(root, "rev-list", "--reverse", head, "--not", "--remotes").splitlines()
    return _changes_for_commits(root, commits)


def root_history_changes(root: Path, head: str) -> list[Change]:
    """Collect the complete available history for an initial remote ref."""
    _require_object(root, head)
    if _is_shallow(root):
        raise GitError("cannot validate an initial ref with incomplete shallow history")
    return _changes_for_commits(root, run_git(root, "rev-list", "--reverse", head).splitlines())


def working_tree_changes(root: Path) -> list[Change]:
    changes: list[Change] = []
    changes.extend(_parse_name_status_z(run_git_bytes(root, "diff", "--name-status", "-z", "--find-renames", "HEAD")))
    changes.extend(_parse_name_status_z(run_git_bytes(root, "diff", "--cached", "--name-status", "-z", "--find-renames", "HEAD")))
    for path in run_git_bytes(root, "ls-files", "-z", "--others", "--exclude-standard").split(b"\0"):
        if path:
            changes.append(Change(path=_decode_path(path), status="A"))
    return _deduplicate(changes)


def pre_push_changes(root: Path, lines: Iterable[str]) -> list[Change]:
    changes: list[Change] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 4:
            raise GitError("invalid pre-push input: expected four fields")
        _local_ref, local_oid, _remote_ref, remote_oid = parts
        if local_oid == ZERO_SHA:
            continue
        if remote_oid == ZERO_SHA:
            changes.extend(new_ref_changes(root, local_oid))
        else:
            changes.extend(range_changes(root, remote_oid, local_oid))
    return _deduplicate(changes)


def rewrite_changes(root: Path, lines: Iterable[str]) -> list[Change]:
    changes: list[Change] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 2:
            raise GitError("invalid post-rewrite input: expected two object IDs")
        changes.extend(range_changes(root, parts[0], parts[1]))
    return _deduplicate(changes)


def ci_event_changes(root: Path, event_name: str, event_path: Path) -> list[Change]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    if event_name == "pull_request":
        return range_changes(root, event["pull_request"]["base"]["sha"], event["pull_request"]["head"]["sha"])
    if event_name == "push":
        base = event.get("before")
        if not base or base == ZERO_SHA:
            return root_history_changes(root, event.get("after", "HEAD"))
        return range_changes(root, base, event.get("after", "HEAD"))
    if event_name == "merge_group":
        group = event["merge_group"]
        return range_changes(root, group.get("base_sha"), group["head_sha"])
    return range_changes(root, None, "HEAD")


def paths(changes: Sequence[Change]) -> list[str]:
    result: list[str] = []
    for change in changes:
        if change.status == "R" and change.old_path:
            result.append(change.old_path.replace("\\", "/"))
        result.append(change.path.replace("\\", "/"))
    return list(dict.fromkeys(result))
