# GitHub Copilot analyzer profiles

Use this reference only when the active host is GitHub Copilot CLI or VS Code with Copilot.

## Project profile

Write one profile per macro-area to `.github/agents/<area>-analyzer.agent.md`. Normalize `<area>` to lowercase ASCII letters, digits, and hyphens. The file must start with YAML frontmatter. Treat it as managed only when its body contains `<!-- Managed by Codebase Analysis AI -->`; never overwrite an unmanaged collision.

```markdown
---
name: <area>-analyzer
description: Read-only analyzer for the <area> macro-area during documentation bootstrap.
tools: [read, search]
user-invocable: false
disable-model-invocation: false
---
<!-- Managed by Codebase Analysis AI -->
Analyze only these repository-relative paths: <paths>.
The invocation brief repeats the allowed and excluded paths and takes the narrower scope.
Return JSON only using the complete contract supplied in that brief.
Do not modify files, propose code fixes, access excluded paths, or delegate to another agent.
```

Keep `tools: [read, search]` explicit because omitted tools default to all available tools. Omitting the `agent` tool also prevents this analyzer from delegating further. `description` is the only host-required frontmatter field, but `name` is required by this skill for deterministic dispatch.

## Discovery and invocation

- Copilot CLI: restart after creating a new profile, then instruct Copilot to use `<area>-analyzer` with the self-contained brief.
- VS Code: ensure the `agent/runSubagent` tool is enabled for the parent request. This is a UI/runtime prerequisite that the skill cannot force; the persistent profile remains valid.
- If the tool is disabled, profile discovery fails, or native invocation fails explicitly, record the cause and use the sequential fallback defined in `subagent-contract.md`.

Sources: [Copilot CLI custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli), [custom agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration), and [VS Code subagents](https://code.visualstudio.com/docs/agents/subagents).
