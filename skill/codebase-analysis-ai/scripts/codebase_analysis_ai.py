#!/usr/bin/env python3
"""Codebase Analysis AI deterministic CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codebase_analysis_ai.documentation_map import MapError, load_map
from codebase_analysis_ai.documentation_preflight import first_documentation_file
from codebase_analysis_ai.git_changes import (
    Change,
    ci_event_changes,
    paths as change_paths,
    pre_push_changes,
    range_changes,
    repository_root,
    rewrite_changes,
    working_tree_changes,
)
from codebase_analysis_ai.impact_graph import resolve_impact
from codebase_analysis_ai.link_validator import validate_links
from codebase_analysis_ai.project_detection import inventory_project
from codebase_analysis_ai.project_installer import InstallConflict, install_project_components
from codebase_analysis_ai.source_hashes import sha256_file
from codebase_analysis_ai.setup_state import inspect_setup
from codebase_analysis_ai.todo_scanner import scan_todos


def _root(value: str) -> Path:
    return repository_root(Path(value).resolve())


def _collect_changes(args: argparse.Namespace, root: Path) -> list[Change]:
    if args.read_pre_push_stdin:
        return pre_push_changes(root, sys.stdin)
    if args.read_rewrite_stdin:
        return rewrite_changes(root, sys.stdin)
    if args.mode == "ci" and args.event_name and args.event_path:
        return ci_event_changes(root, args.event_name, Path(args.event_path))
    if args.base or args.head:
        return range_changes(root, args.base, args.head or "HEAD")
    return working_tree_changes(root)


def command_check(args: argparse.Namespace) -> int:
    root = _root(args.root)
    try:
        documentation_map = load_map(root)
    except MapError as exc:
        print(f"Codebase Analysis AI: {exc}", file=sys.stderr)
        print("Run an explicit documentation bootstrap or migration before incremental checks.", file=sys.stderr)
        return 0 if args.warn_only else 2

    map_errors = documentation_map.validate()
    changes = _collect_changes(args, root)
    changed_paths = change_paths(changes)
    impact = resolve_impact(documentation_map, changed_paths)

    stale: list[str] = []
    for path in changed_paths:
        current = sha256_file(root / path)
        for doc_id in documentation_map.matching_documents(path):
            recorded = documentation_map.documents[doc_id].get("sourceHashes", {}).get(path)
            if recorded != current:
                stale.append(f"{path} -> {doc_id}")

    document_paths = [
        documentation_map.documents[doc_id]["path"]
        for doc_id in impact.all_documents
        if doc_id in documentation_map.documents and documentation_map.documents[doc_id].get("path")
    ]
    link_errors = validate_links(root, document_paths)
    errors = [*map_errors, *[f"Unmapped source: {path}" for path in impact.unmapped], *[f"Stale: {item}" for item in stale], *link_errors]

    report = {
        "mode": args.mode,
        "changedFiles": changed_paths,
        "directDocuments": list(impact.direct),
        "relatedDocuments": list(impact.related),
        "unmappedFiles": list(impact.unmapped),
        "staleMappings": stale,
        "linkErrors": link_errors,
        "mapErrors": map_errors,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    elif errors:
        print("Codebase Analysis AI failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        if impact.all_documents:
            print("Impacted documents:", file=sys.stderr)
            for doc_id in impact.all_documents:
                print(f"- {doc_id}", file=sys.stderr)
    else:
        print("Codebase Analysis AI: documentation is synchronized for the selected changes.")

    if errors and not args.warn_only:
        return 1
    return 0


def command_refresh(args: argparse.Namespace) -> int:
    root = _root(args.root)
    documentation_map = load_map(root)
    selected = [path.replace("\\", "/") for path in args.paths]
    if not selected:
        selected = change_paths(working_tree_changes(root))
    refreshed: list[str] = []
    for path in selected:
        for doc_id in documentation_map.matching_documents(path):
            hashes = documentation_map.documents[doc_id].setdefault("sourceHashes", {})
            hashes[path] = sha256_file(root / path)
            refreshed.append(f"{path} -> {doc_id}")
    documentation_map.save()
    print(json.dumps({"refreshed": sorted(set(refreshed))}, indent=2))
    return 0


def command_detect(args: argparse.Namespace) -> int:
    print(json.dumps(inventory_project(_root(args.root)), indent=2))
    return 0


def command_docs_state(args: argparse.Namespace) -> int:
    root = _root(args.root)
    first = first_documentation_file(root)
    print(json.dumps({
        "documentationState": "present" if first else "none",
        "firstDocument": str(first.relative_to(root)).replace("\\", "/") if first else None,
    }, indent=2))
    return 0


def command_setup_state(args: argparse.Namespace) -> int:
    print(json.dumps(inspect_setup(_root(args.root), args.agents), indent=2))
    return 0


def command_todos(args: argparse.Namespace) -> int:
    root = _root(args.root)
    print(json.dumps(scan_todos(root, args.paths), indent=2))
    return 0


def command_install(args: argparse.Namespace) -> int:
    root = _root(args.root)
    agents = ["codex", "claude", "gemini", "copilot"] if "all" in args.agents else args.agents
    try:
        changed = install_project_components(root, agents, args.with_agent_rules, args.with_hooks, args.with_github_action)
    except InstallConflict as exc:
        print(f"Codebase Analysis AI setup stopped: {exc}", file=sys.stderr)
        return 2
    print("Codebase Analysis AI setup completed:")
    for path in changed:
        print(f"- {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental repository documentation checks and setup")
    parser.add_argument("--root", default=".", help="Path inside the target Git repository")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check documentation freshness and links")
    check.add_argument("--mode", default="working-tree", choices=["working-tree", "post-commit", "pre-push", "post-merge", "post-rewrite", "ci"])
    check.add_argument("--base")
    check.add_argument("--head")
    check.add_argument("--event-name")
    check.add_argument("--event-path")
    check.add_argument("--read-pre-push-stdin", action="store_true")
    check.add_argument("--read-rewrite-stdin", action="store_true")
    check.add_argument("--warn-only", action="store_true")
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=command_check)

    refresh = subparsers.add_parser("refresh", help="Refresh source hashes after documentation was reviewed")
    refresh.add_argument("paths", nargs="*")
    refresh.set_defaults(handler=command_refresh)

    detect = subparsers.add_parser("detect", help="Collect bounded structural project evidence")
    detect.set_defaults(handler=command_detect)

    docs_state = subparsers.add_parser(
        "docs-state", help="Detect existing documentation without reading its contents"
    )
    docs_state.set_defaults(handler=command_docs_state)

    setup_state = subparsers.add_parser("setup-state", help="Inspect project setup without changing files")
    setup_state.add_argument("--agents", nargs="+", default=["codex"], choices=["codex", "claude", "gemini", "copilot", "all"])
    setup_state.set_defaults(handler=command_setup_state)

    todos = subparsers.add_parser("todos", help="Scan selected files for TODO evidence")
    todos.add_argument("paths", nargs="+")
    todos.set_defaults(handler=command_todos)

    install = subparsers.add_parser("install", help="Install project automation components")
    install.add_argument("--agents", nargs="+", default=["codex"], choices=["codex", "claude", "gemini", "copilot", "all"])
    install.add_argument("--with-agent-rules", action="store_true")
    install.add_argument("--with-hooks", action="store_true")
    install.add_argument("--with-github-action", action="store_true")
    install.set_defaults(handler=command_install)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (MapError, OSError, RuntimeError) as exc:
        print(f"Codebase Analysis AI error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
