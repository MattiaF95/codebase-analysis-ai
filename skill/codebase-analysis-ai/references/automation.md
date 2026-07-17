# Automation

Automation has three independent layers:

1. Agent rules tell the active coding agent to run the checker after relevant changes.
2. Git hooks provide local warnings and pre-push enforcement.
3. GitHub Actions provide the shared PR, merge-queue, and default-branch gate.

The deterministic checker never invokes an AI model.

## Initial automation proposal

After `setup-state`, always include automation in the single initial contract. For the runtime, each active-host adapter, every hook, and the GitHub Action, report one proposed action: `create`, `add`, `refresh`, `keep`, `skip`, or `resolve conflict`. Briefly explain the operational effect and ask for confirmation even when the proposal contains only `keep` actions.

Missing managed components may be created or added. Existing managed components may be refreshed from the current templates after confirmation. Unmanaged or conflicting files must not be overwritten; identify the exact path and propose only a repository-supported integration or a skip.

## Agent rules

Install a managed block in the instruction file for each selected host. Do not duplicate the skill body. Preserve unrelated instructions.

## Hooks

- `post-commit`: warn after stale changes are committed.
- `pre-push`: block only when unprocessed impact remains.
- `post-merge`: warn after merge-based pulls.
- `post-rewrite`: warn after rebase, amend, or pull with rebase.

Store hooks under `.githooks/` and configure the local clone with `git config core.hooksPath .githooks`. Add missing managed hooks and refresh existing managed hooks only after confirmation. Stop if an unrecognized existing hook would be replaced.

## GitHub Action

Install `.github/workflows/codebase-analysis-ai.yml` with read-only contents permission. Cover Pull Request updates, merge groups, default-branch pushes, and manual dispatch. Do not add model credentials or automatic commits.

Create the workflow when absent and refresh it when it carries the managed marker. If the dedicated path is unmanaged, report the conflict and do not overwrite it. Other workflows do not prevent creating the dedicated workflow unless repository evidence shows duplicate or conflicting enforcement.
