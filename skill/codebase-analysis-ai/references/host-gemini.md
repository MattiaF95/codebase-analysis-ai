# Gemini CLI analyzer profiles

Use this reference only when the active host is Gemini CLI.

## Project profile

Write one profile per macro-area to `.gemini/agents/<area>-analyzer.md`. Normalize `<area>` to lowercase ASCII letters, digits, hyphens, and underscores. The file must start with YAML frontmatter. Treat it as managed only when its body contains `<!-- Managed by Codebase Analysis AI -->`; never overwrite an unmanaged collision.

```markdown
---
name: <area>-analyzer
description: Read-only analyzer for the <area> macro-area during documentation bootstrap.
kind: local
tools:
  - read_file
  - glob
  - grep_search
  - list_directory
---
<!-- Managed by Codebase Analysis AI -->
Analyze only these repository-relative paths: <paths>.
The invocation brief repeats the allowed and excluded paths and takes the narrower scope.
Return JSON only using the complete contract supplied in that brief.
Do not modify files, propose code fixes, access excluded paths, or delegate to another agent.
```

`name` and `description` are required. Keep the read-only `tools` allowlist explicit because omission inherits the parent tools. Use `grep_search`; `search_file_content` is only a legacy alias.

## Discovery and invocation

- Subagents are enabled by default. Do not add the obsolete `experimental.enableSubagents` setting. If `experimental.enableAgents` is explicitly `false`, report the disabled capability instead of silently changing user settings.
- Run `/agents refresh` (alias of `/agents reload`), verify with `/agents list`, then invoke explicitly as `@<area>-analyzer <brief>`. `/agents enable <name>` and `/agents disable <name>` control individual profiles.
- If refresh, discovery, or invocation fails explicitly, record the error and use the sequential fallback defined in `subagent-contract.md`.

Sources: [Gemini CLI subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md), [commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/commands.md), and [tools](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/tools.md).
