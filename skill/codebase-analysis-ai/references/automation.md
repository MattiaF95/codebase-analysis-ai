# Automation

Automation has three independent layers:

1. Agent rules tell the active coding agent to run the checker after relevant changes.
2. Git hooks provide local warnings and pre-push enforcement.
3. GitHub Actions provide the shared PR, merge-queue, and default-branch gate.

The deterministic checker never invokes an AI model.

## Agent rules

Install a managed block in the instruction file for each selected host. Do not duplicate the skill body. Preserve unrelated instructions.

## Hooks

- `post-commit`: warn after stale changes are committed.
- `pre-push`: block only when unprocessed impact remains.
- `post-merge`: warn after merge-based pulls.
- `post-rewrite`: warn after rebase, amend, or pull with rebase.

Store hooks under `.githooks/` and configure the local clone with `git config core.hooksPath .githooks`. Stop if an unrecognized existing hook would be replaced.

## GitHub Action

Install `.github/workflows/codebase-analysis-ai.yml` with read-only contents permission. Cover Pull Request updates, merge groups, default-branch pushes, and manual dispatch. Do not add model credentials or automatic commits.

