"""Read-only inspection of Codebase Analysis AI project setup."""

from __future__ import annotations

import subprocess
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
RUNTIME_MARKER = "Codebase Analysis AI deterministic CLI."


def _file_state(path: Path, expected: str | None = None) -> str:
    if not path.exists():
        return "absent"
    content = path.read_text(encoding="utf-8", errors="replace")
    if MANAGED not in content:
        return "unmanaged"
    return "outdated" if expected is not None and content != expected else "managed"


def _adapter_state(path: Path, agent: str, expected_block: str | None = None) -> str:
    if not path.exists():
        return "absent"
    content = path.read_text(encoding="utf-8", errors="replace")
    expected = f"setup-state --agents {agent}"
    if START not in content:
        return "unmanaged"
    if expected not in content or (expected_block is not None and expected_block.strip() not in content):
        return "outdated"
    return "managed"


def _runtime_state(root: Path) -> str:
    target = root / "tools" / "codebase-analysis-ai"
    check = target / "check.py"
    if not check.is_file():
        return "absent"
    if RUNTIME_MARKER not in check.read_text(encoding="utf-8", errors="replace"):
        return "unmanaged"
    source_scripts = Path(__file__).resolve().parent.parent
    source_check = source_scripts / "codebase_analysis_ai.py"
    if source_check.is_file() and source_check.read_bytes() != check.read_bytes():
        return "outdated"
    for source in (source_scripts / "codebase_analysis_ai").rglob("*.py"):
        relative = source.relative_to(source_scripts / "codebase_analysis_ai")
        installed = target / "codebase_analysis_ai" / relative
        if not installed.is_file() or installed.read_bytes() != source.read_bytes():
            return "outdated"
    return "managed"


def _default_branch(root: Path) -> str:
    for command in (
        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        ["git", "branch", "--show-current"],
    ):
        result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        if result.stdout.strip():
            return result.stdout.strip().removeprefix("origin/")
    return "main"


def inspect_setup(root: Path, agents: list[str]) -> dict[str, object]:
    root = root.resolve()
    skill_root = Path(__file__).resolve().parents[2]
    assets = skill_root / "assets"
    has_assets = assets.is_dir()
    requested_agents = ["codex", "claude", "gemini", "copilot"] if "all" in agents else list(dict.fromkeys(agents))
    adapter_assets = {
        "codex": "AGENTS.md",
        "claude": "CLAUDE.md",
        "gemini": "GEMINI.md",
        "copilot": "copilot-instructions.md",
    }
    adapters = {
        agent: _adapter_state(
            root / AGENT_TARGETS[agent],
            agent,
            (assets / "adapters" / adapter_assets[agent]).read_text(encoding="utf-8") if has_assets else None,
        )
        for agent in requested_agents
    }

    hooks = {
        name: _file_state(
            root / ".githooks" / name,
            (assets / "hooks" / name).read_text(encoding="utf-8") if has_assets else None,
        )
        for name in HOOKS
    }
    expected_action = None
    if has_assets:
        expected_action = (assets / "workflows" / "codebase-analysis-ai.yml").read_text(encoding="utf-8")
        expected_action = expected_action.replace("__DEFAULT_BRANCH__", _default_branch(root))
    action = _file_state(root / ".github" / "workflows" / "codebase-analysis-ai.yml", expected_action)

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
                    if sha256_file(source) != recorded:
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
        "runtime": _runtime_state(root),
        "adapters": adapters,
        "hooks": hooks,
        "githubAction": action,
        "documentation": docs,
    }
