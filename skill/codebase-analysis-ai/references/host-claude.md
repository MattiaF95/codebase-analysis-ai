# Claude Code analyzer profiles

Use this reference only when the active host is Claude Code.

## Project profile

Write one profile per macro-area to `.claude/agents/<area>-analyzer.md`. Normalize `<area>` to lowercase ASCII letters, digits, and hyphens. The file must start with YAML frontmatter. Treat it as managed only when its body contains `<!-- Managed by Codebase Analysis AI -->`; never overwrite an unmanaged collision.

```markdown
---
name: <area>-analyzer
description: Use this agent to review the <area> macro-area during documentation bootstrap.
tools: Read, Grep, Glob
model: inherit
---
<!-- Managed by Codebase Analysis AI -->
Analyze only these repository-relative paths: <paths>.
The invocation brief repeats the allowed and excluded paths and takes the narrower scope.
Return JSON only using the complete contract supplied in that brief.
Do not modify files, propose code fixes, access excluded paths, or delegate to another agent.
```

`name` and `description` are required. Keep the `tools` allowlist explicit; omitting it inherits the parent toolset. `Read`, `Grep`, and `Glob` provide analysis without `Write`, `Edit`, `Bash`, MCP, or agent delegation tools.

## Discovery and invocation

- Refer to `<area>-analyzer` explicitly in the prompt or through an @-mention when available.
- Claude Code normally watches existing agent directories. Restart only when the session created its first `.claude/agents/` directory or directory watching is disabled.
- If discovery or invocation fails after the required restart, record the error and use the sequential fallback defined in `subagent-contract.md`.

Source: [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).
