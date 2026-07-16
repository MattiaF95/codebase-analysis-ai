# Codex analyzer profiles

Use this reference only when the active host is Codex.

## Project profile

Write one profile per macro-area to `.codex/agents/<area>-analyzer.toml`. Normalize `<area>` to lowercase ASCII letters, digits, and hyphens. Treat a file as managed only when it contains `# Managed by Codebase Analysis AI`; never overwrite an unmanaged collision.

```toml
# Managed by Codebase Analysis AI
name = "<area>-analyzer"
description = "Read-only analyzer for the <area> macro-area during documentation bootstrap."
sandbox_mode = "read-only"
developer_instructions = """
Analyze only these repository-relative paths: <paths>.
The invocation brief repeats the allowed and excluded paths and takes the narrower scope.
Return JSON only using the complete contract supplied in that brief.
Do not write files, propose code fixes, access excluded paths, or delegate to another agent.
"""
```

`name`, `description`, and `developer_instructions` are required. Keep `sandbox_mode = "read-only"` explicit because omitted settings inherit from the parent session. Live parent permission overrides can still take precedence, so the parent must verify that the analyzer produced no working-tree changes.

## Discovery and invocation

- No feature flag is required. Ask Codex directly to spawn `<area>-analyzer` with the self-contained brief.
- Run independent analyzers in parallel within the host concurrency limit, then wait for every dispatched result before merging.
- If profile creation or native invocation fails explicitly, record the error and use the sequential fallback defined in `subagent-contract.md`.

Source: [Codex subagents](https://developers.openai.com/codex/subagents).
