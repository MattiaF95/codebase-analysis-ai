# Setup mode

Use setup mode after an explicit setup request or after the user confirms a setup phase in the initial contract, including when the mandatory preflight finds missing runtime or host integration.

## Procedure

1. Resolve the target repository root.
2. Inspect existing skill locations, agent instruction files, `core.hooksPath`, `.git/hooks`, `.githooks`, Husky, Lefthook, pre-commit frameworks, and `.github/workflows`.
3. Build an adaptive proposal for every component and include it in the single initial confirmation: create absent runtime, rules, hooks, or workflow; add missing managed hooks; refresh managed components from current templates; keep current components unchanged when no refresh is needed; and report unmanaged conflicts without overwriting them.
4. Explain that hooks enforce local checks and the GitHub Action provides shared pull-request, merge-queue, and default-branch checks. Ask for confirmation even when all components already exist; a no-change proposal is valid.
5. After confirmation, run `scripts/codebase_analysis_ai.py install` with matching flags. Managed hooks and the managed GitHub Action may be refreshed; unrecognized files must never be replaced.
6. Stop on unrecognized hook or workflow conflicts and request a revised plan. Do not invent chaining or framework integration without repository evidence.
7. Run the deterministic checker and installer tests.
8. Report every created, updated, retained, skipped, or conflicted component and any local-only Git configuration.

Setup must be idempotent. Re-running it must update managed blocks without duplication and preserve unrelated instructions.
