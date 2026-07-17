<!-- codebase-analysis-ai:start -->
## Documentation maintenance

After changing application behavior, APIs, schemas, security, configuration, deployment, pipelines, or architectural flows:

1. Read `docs/index.md` before any other documentation when it exists; use it to open only the files required by the task.
2. Run `python tools/codebase-analysis-ai/check.py setup-state --agents claude`, then `python tools/codebase-analysis-ai/check.py check --mode working-tree`.
3. If no documentation is impacted, do not invoke the skill.
4. If documentation is stale, invoke `/codebase-analysis-ai` in incremental update mode.
5. Inspect only changed source files, mapped documents, and their direct first-level links.
6. Verify `docs/index.md` on every documentation change and update it when navigation, paths, or document purposes change.
7. Never scan the entire repository unless the user explicitly requests a full documentation bootstrap.
8. If `docs/` does not exist and bootstrap was not explicit, ask whether to initialize documentation or stop.
9. Do not invent active functionality, TODOs, commands, dependencies, or architectural relationships.
10. Preserve manual content outside managed sections.
<!-- codebase-analysis-ai:end -->
