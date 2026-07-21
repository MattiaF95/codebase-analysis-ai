# Setup mode

Use setup mode after an explicit setup request or after the user confirms a setup phase in the initial contract, including when the mandatory preflight finds missing runtime or host integration.

## Procedure

1. Resolve the target repository root.
2. Inspect existing skill locations, agent instruction files, `core.hooksPath`, `.git/hooks`, `.githooks`, Husky, Lefthook, pre-commit frameworks, and `.github/workflows`.
3. Build an adaptive proposal for every component and include it in the single initial confirmation. Missing components are mandatory: create the runtime, the selected agent rule file, exactly the four skill hooks, and the dedicated workflow. Refresh outdated managed runtime, agent blocks, hooks, and workflow after confirmation; preserve manual agent text and report unmanaged conflicts without overwriting them.
4. Explain that hooks enforce local checks and the GitHub Action provides shared pull-request, merge-queue, and default-branch checks. Ask for confirmation even when all components already exist; a no-change proposal is valid.
5. Run setup discovery and installation with the current bundled skill command so an outdated project runtime cannot validate or refresh itself. After confirmation, run from the target repository root:

   `python <installed-skill-root>/scripts/codebase_analysis_ai.py --root . install --agents <active-host>`

   The command creates missing components and refreshes outdated managed components. It never replaces unmanaged runtime, hooks, workflows, agent instructions, or unrelated automation.
6. Stop on unrecognized hook or workflow conflicts and request a revised plan. Do not invent chaining or framework integration without repository evidence.
7. Run the deterministic checker and installer tests.
8. Report every created, refreshed, retained, or conflicted component and any local-only Git configuration. Do not classify agent rule files or installed automation as project documentation.

Setup must be idempotent. Re-running it must preserve current managed components, refresh only outdated managed content, and preserve unrelated instructions and automation.
