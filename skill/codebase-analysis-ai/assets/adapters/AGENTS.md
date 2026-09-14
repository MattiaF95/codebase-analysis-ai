<!-- codebase-analysis-ai:start -->
## Documentation maintenance

After changing application behavior, APIs, schemas, security, configuration, deployment, pipelines, or architectural flows:

1. Read `docs/index.md` before any other documentation when it exists; use it to open only the files required by the task.
2. Run `python3 <installed-skill-root>/scripts/codebase_analysis_ai.py --root . setup-state --agents codex`, then, only when the runtime is current, run `python3 tools/codebase-analysis-ai/check.py check --mode working-tree` (`py -3` on Windows).
3. If no documentation is impacted, do not invoke the skill.
4. If documentation is stale, invoke `$codebase-analysis-ai` in incremental update mode.
5. Inspect only changed source files, mapped documents, and their direct first-level links.
6. Verify `docs/index.md` on every documentation change and update it when navigation, paths, or document purposes change.
7. Never scan the entire repository unless the user explicitly requests a full documentation bootstrap.
8. If `docs/` does not exist and bootstrap was not explicit, ask whether to initialize documentation or stop.
9. Do not invent active functionality, TODOs, commands, dependencies, or architectural relationships.
10. Preserve manual content outside managed sections.
11. A manually changed Markdown document is immediately accepted as valid: record it as `changedDocuments`, preserve its content, and do not update documentation or source hashes automatically.

## Hook interruption protocol

When any `git` command starts an output-producing hook, reports a hook failure, or returns a non-zero hook status:

1. Stop immediately. Do not continue with commit, push, merge, rebase, amend, or any other Git operation.
2. Read and preserve the complete JSON report emitted by the hook, including `mode`, `changedFiles`, `changedDocuments`, stale mappings, unmapped files, link errors, and exit status. This report is the authoritative context; never replace it with a `working-tree` check.
3. For `post-commit`, rerun only when needed with exactly `python3 tools/codebase-analysis-ai/check.py check --mode post-commit --head HEAD --json`; omitting `--base` works for both root and later commits. For `pre-push`, `post-merge`, and `post-rewrite`, analyze the captured hook report because their original stdin or refs may no longer be reproducible.
4. Fix or report the cause, and only resume the interrupted Git flow after the relevant check is clean or the user explicitly accepts a warning-only result.

Never classify hook output as irrelevant. A `post-commit` warning still requires analysis; a failing `pre-push` is a publication block.
<!-- codebase-analysis-ai:end -->
