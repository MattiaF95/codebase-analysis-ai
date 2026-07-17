<!-- codebase-analysis-ai:start -->
## Documentation maintenance

After changing application behavior, APIs, schemas, security, configuration, deployment, pipelines, or architectural flows:

1. Run `python tools/codebase-analysis-ai/check.py setup-state --agents codex`, then `python tools/codebase-analysis-ai/check.py check --mode working-tree`.
2. If no documentation is impacted, do not invoke the skill.
3. If documentation is stale, invoke `$codebase-analysis-ai` in incremental update mode.
4. Inspect only changed source files, mapped documents, and their direct first-level links.
5. Never scan the entire repository unless the user explicitly requests a full documentation bootstrap.
6. If `docs/` does not exist and bootstrap was not explicit, ask whether to initialize documentation or stop.
7. Do not invent active functionality, TODOs, commands, dependencies, or architectural relationships.
8. Preserve manual content outside managed sections.
<!-- codebase-analysis-ai:end -->
