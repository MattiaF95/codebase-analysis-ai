# Automation

Automation has three independent layers:

1. Agent rules tell the active coding agent to run the checker after relevant changes.
2. Git hooks provide local warnings and pre-push enforcement.
3. GitHub Actions provide the shared PR, merge-queue, and default-branch gate.

The deterministic checker never invokes an AI model.

## Initial automation proposal

After `setup-state`, always include automation in the single initial contract. For the runtime, each active-host adapter, every required hook, and the GitHub Action, report one proposed action: `create`, `refresh`, `keep`, or `resolve conflict`. Missing components must be proposed as `create`, outdated managed components as `refresh`, current managed components as `keep`, and unmanaged collisions as `resolve conflict`. Briefly explain the operational effect and ask for confirmation once for the complete contract.

Missing managed components must be created and outdated managed components refreshed after setup confirmation. Unmanaged or conflicting files must not be overwritten; identify the exact path and stop setup for that component.

## Agent rules

Install or refresh the managed block in the instruction file for each selected host. Do not duplicate the skill body. Preserve unrelated instructions.

## Hooks

- `post-commit`: warn after stale changes are committed.
- `pre-push`: block only when unprocessed impact remains.
- `post-merge`: warn after merge-based pulls.
- `post-rewrite`: warn after rebase, amend, or pull with rebase.

Every hook invokes the checker with `--json`. When an agent runs a Git command and any hook produces output or a non-zero status, the agent must stop the Git flow and preserve and analyze that complete JSON report as the authoritative execution context. It must never substitute a generic `working-tree` check after a commit or push attempt.

The agent may rerun `post-commit` with `python tools/codebase-analysis-ai/check.py check --mode post-commit --base HEAD^ --head HEAD --json` while `HEAD` is unchanged. For `pre-push`, `post-merge`, and `post-rewrite`, use the captured report because their original stdin or refs may no longer be reproducible. Do not continue with another Git operation until the relevant result is clean or the user explicitly accepts a warning-only result. Hook output is never irrelevant: warnings require analysis, and a failing `pre-push` blocks publication.

Store exactly these hooks under `.githooks`: `post-commit`, `pre-push`, `post-merge`, and `post-rewrite`. Configure the local clone with `git config core.hooksPath .githooks`. Create `.githooks` and each missing hook after confirmation, and refresh outdated hooks only when they retain the managed marker. If `core.hooksPath` points to a missing path, treat it as stale and repair it; if it points to an existing different path, stop on conflict. Do not create or modify other hooks.

## GitHub Action

Install `.github/workflows/codebase-analysis-ai.yml` with read-only contents permission. Cover Pull Request updates, merge groups, default-branch pushes, and manual dispatch. Do not add model credentials or automatic commits.

Create the workflow when absent and refresh it when outdated and managed. If the dedicated path is unmanaged, report the conflict and do not overwrite it. Other workflows do not prevent creating the dedicated workflow, and must never be modified.
