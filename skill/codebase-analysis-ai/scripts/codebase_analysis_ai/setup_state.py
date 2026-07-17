"""Read-only inspection of Codebase Analysis AI project setup."""

from __future__ import annotations

from pathlib import Path

from .documentation_map import MapError, load_map
from .documentation_preflight import first_documentation_file
from .source_hashes import sha256_file


AGENT_TARGETS = {
    "codex": "AGENTS.md",
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "copilot": ".github/copilot-instructions.md",
}
HOOKS = ("post-commit", "pre-push", "post-merge", "post-rewrite")
MANAGED = "Managed by Codebase Analysis AI."
START = "<!-- codebase-analysis-ai:start -->"


def _file_state(path: Path) -> str:
    if not path.exists():
        return "absent"
    return "managed" if MANAGED in path.read_text(encoding="utf-8", errors="replace") else "unmanaged"


def _adapter_state(path: Path, agent: str) -> str:
    if not path.exists():
        return "absent"
    content = path.read_text(encoding="utf-8", errors="replace")
    expected = f"setup-state --agents {agent}"
    return "managed" if START in content and expected in content else "outdated" if START in content else "unmanaged"


def inspect_setup(root: Path, agents: list[str]) -> dict[str, object]:
    root = root.resolve()
    runtime = root / "tools" / "codebase-analysis-ai" / "check.py"
    requested_agents = ["codex", "claude", "gemini", "copilot"] if "all" in agents else list(dict.fromkeys(agents))
    adapters = {agent: _adapter_state(root / AGENT_TARGETS[agent], agent) for agent in requested_agents}

    hooks = {name: _file_state(root / ".githooks" / name) for name in HOOKS}
    action = _file_state(root / ".github" / "workflows" / "codebase-analysis-ai.yml")

    first_doc = first_documentation_file(root)
    docs: dict[str, object] = {
        "state": "none" if first_doc is None else "present",
        "firstDocument": str(first_doc.relative_to(root)).replace("\\", "/") if first_doc else None,
    }
    map_path = root / "docs" / "_meta" / "documentation-map.json"
    if map_path.exists():
        try:
            documentation_map = load_map(root)
            errors = documentation_map.validate()
            missing = [document.get("path") for document in documentation_map.documents.values()
                       if document.get("path") and not (root / document["path"]).is_file()]
            stale = []
            for document in documentation_map.documents.values():
                for source_path, recorded in document.get("sourceHashes", {}).items():
                    source = root / source_path
                    if source.is_file() and sha256_file(source) != recorded:
                        stale.append(source_path)
            docs["state"] = "incoherent" if errors or missing else "stale" if stale else "coherent"
            docs["mapErrors"] = errors
            docs["missingDocuments"] = missing
            docs["staleSources"] = sorted(set(stale))
        except (MapError, OSError, ValueError):
            docs["state"] = "incoherent"
    elif first_doc is not None:
        docs["state"] = "not-indexed"

    return {
        "runtime": "present" if runtime.is_file() else "absent",
        "adapters": adapters,
        "hooks": hooks,
        "githubAction": action,
        "documentation": docs,
    }
