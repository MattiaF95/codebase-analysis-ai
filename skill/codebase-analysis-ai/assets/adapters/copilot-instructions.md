<!-- codebase-analysis-ai:start -->
## Documentation maintenance

After changing application behavior, APIs, schemas, security, configuration, deployment, pipelines, or architectural flows:

1. Read `docs/index.md` before any other documentation when it exists; use it to open only the files required by the task.
2. Run `python tools/codebase-analysis-ai/check.py setup-state --agents copilot`, then `python tools/codebase-analysis-ai/check.py check --mode working-tree`.
3. If no documentation is impacted, do not invoke the skill.
4. If documentation is stale, ask Copilot to activate `codebase-analysis-ai` in incremental update mode.
5. Inspect only changed source files, mapped documents, and their direct first-level links.
6. Verify `docs/index.md` on every documentation change and update it when navigation, paths, or document purposes change.
7. Never scan the entire repository unless the user explicitly requests a full documentation bootstrap.
8. If `docs/` does not exist and bootstrap was not explicit, ask whether to initialize documentation or stop.
9. Do not invent active functionality, TODOs, commands, dependencies, or architectural relationships.
10. Preserve manual content outside managed sections.

## Hook interruption protocol

When any `git` command starts an output-producing hook, reports a hook failure, or returns a non-zero hook status:

1. Stop immediately. Do not continue with commit, push, merge, rebase, amend, or any other Git operation.
2. Read and preserve the complete hook output, identify the hook name and exit status, then run exactly:
   `python tools/codebase-analysis-ai/check.py check --mode working-tree --json`
3. Analyze the command output and the hook output, fix or report the cause, and only resume the interrupted Git flow after the check is clean or the user explicitly accepts a warning-only result.

Never classify hook output as irrelevant. A `post-commit` warning still requires analysis; a failing `pre-push` is a publication block.
<!-- codebase-analysis-ai:end -->
