# Automation

Automation has three independent layers:

1. Agent rules tell the active coding agent to run the checker after relevant changes.
2. Git hooks provide local warnings and pre-push enforcement.
3. GitHub Actions provide the shared PR, merge-queue, and default-branch gate.

The deterministic checker never invokes an AI model.

## Initial automation proposal

After `setup-state`, always include automation in the single initial contract. For the runtime, each active-host adapter, every required hook, and the GitHub Action, report one proposed action: `create`, `keep`, or `resolve conflict`. Missing components must be proposed as `create`; existing components as `keep`. Briefly explain the operational effect and ask for confirmation once for the complete contract.

Missing managed components must be created after setup confirmation. Existing agent files, hooks, and the dedicated workflow are retained unchanged. Unmanaged or conflicting files must not be overwritten; identify the exact path and stop setup for that component.

## Agent rules

Install a managed block in the instruction file for each selected host. Do not duplicate the skill body. Preserve unrelated instructions.

## Hooks

- `post-commit`: warn after stale changes are committed.
- `pre-push`: block only when unprocessed impact remains.
- `post-merge`: warn after merge-based pulls.
- `post-rewrite`: warn after rebase, amend, or pull with rebase.

Store exactly these hooks under `.githooks`: `post-commit`, `pre-push`, `post-merge`, and `post-rewrite`. Configure the local clone with `git config core.hooksPath .githooks`. Create each missing hook after confirmation. Preserve every existing hook unchanged and stop if the dedicated path is an unmanaged conflict. Do not create or modify other hooks.

## GitHub Action

Install `.github/workflows/codebase-analysis-ai.yml` with read-only contents permission. Cover Pull Request updates, merge groups, default-branch pushes, and manual dispatch. Do not add model credentials or automatic commits.

Create the workflow when absent and preserve it unchanged when present. If the dedicated path is unmanaged, report the conflict and do not overwrite it. Other workflows do not prevent creating the dedicated workflow, and must never be modified.
