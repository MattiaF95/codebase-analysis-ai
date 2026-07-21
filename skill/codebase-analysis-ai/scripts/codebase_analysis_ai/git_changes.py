"""Collect repository-relative changes from Git."""

from __future__ import annotations

import json
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
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


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


def _deduplicate(changes: Iterable[Change]) -> list[Change]:
    merged: dict[str, Change] = {}
    for change in changes:
        merged[change.path] = change
    return sorted(merged.values(), key=lambda item: item.path)


def range_changes(root: Path, base: str | None, head: str = "HEAD") -> list[Change]:
    if not base:
        output = run_git(root, "diff-tree", "--root", "--no-commit-id", "--name-status", "-r", head)
    else:
        output = run_git(root, "diff", "--name-status", "--find-renames", base, head)
    return _parse_name_status(output)


def new_ref_changes(root: Path, head: str) -> list[Change]:
    """Collect every commit introduced by a ref that does not yet exist remotely."""
    commits = run_git(root, "rev-list", "--reverse", head, "--not", "--remotes").splitlines()
    changes: list[Change] = []
    for commit in commits:
        output = run_git(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-status",
            "--find-renames",
            "-r",
            commit,
        )
        changes.extend(_parse_name_status(output))
    return _deduplicate(changes)


def working_tree_changes(root: Path) -> list[Change]:
    changes: list[Change] = []
    changes.extend(_parse_name_status(run_git(root, "diff", "--name-status", "--find-renames", "HEAD")))
    changes.extend(_parse_name_status(run_git(root, "diff", "--cached", "--name-status", "--find-renames", "HEAD")))
    for path in run_git(root, "ls-files", "--others", "--exclude-standard").splitlines():
        if path.strip():
            changes.append(Change(path=path.strip(), status="A"))
    return _deduplicate(changes)


def pre_push_changes(root: Path, lines: Iterable[str]) -> list[Change]:
    changes: list[Change] = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 4:
            continue
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
        parts = line.strip().split()
        if len(parts) >= 2:
            changes.extend(range_changes(root, parts[0], parts[1]))
    return _deduplicate(changes)


def ci_event_changes(root: Path, event_name: str, event_path: Path) -> list[Change]:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    if event_name == "pull_request":
        return range_changes(root, event["pull_request"]["base"]["sha"], event["pull_request"]["head"]["sha"])
    if event_name == "push":
        base = event.get("before")
        if not base or base == ZERO_SHA:
            return new_ref_changes(root, event.get("after", "HEAD"))
        return range_changes(root, base, event.get("after", "HEAD"))
    if event_name == "merge_group":
        group = event["merge_group"]
        return range_changes(root, group.get("base_sha"), group["head_sha"])
    return range_changes(root, "HEAD^", "HEAD")


def paths(changes: Sequence[Change]) -> list[str]:
    result: list[str] = []
    for change in changes:
        if change.status == "R" and change.old_path:
            result.append(change.old_path.replace("\\", "/"))
        result.append(change.path.replace("\\", "/"))
    return list(dict.fromkeys(result))
