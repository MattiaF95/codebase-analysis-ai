# Setup mode

Use setup mode after an explicit request to configure Codebase Analysis AI in a target repository, including when the mandatory preflight finds missing runtime or host integration.

## Procedure

1. Resolve the target repository root.
2. Inspect existing skill locations, agent instruction files, `core.hooksPath`, `.git/hooks`, `.githooks`, Husky, Lefthook, pre-commit frameworks, and `.github/workflows`.
3. Select only requested components: skill, agent rules, runtime checker, hooks, or GitHub Action. Hooks and the GitHub Action require separate explicit confirmation when absent.
4. Run `scripts/codebase_analysis_ai.py install` with matching flags.
5. Stop on unrecognized hook or workflow conflicts. Never replace existing hooks or workflows silently; already-present managed components are left unchanged.
6. Run the deterministic checker and installer tests.
7. Report every created or modified file and any local-only Git configuration.

Setup must be idempotent. Re-running it must update managed blocks without duplication and preserve unrelated instructions.
