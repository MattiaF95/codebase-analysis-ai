# PlanVault bridge

PlanVault is an optional execution-plan format. The documentation system recognizes it when it is present but never requires it, installs it, or edits its files. Plans remain owned by the planning workflow; ADRs remain owned by the documentation workflow.

## Detection

The deterministic tools recognize two shapes under `plans/`:

- single-file plans: any `plans/**/*.md` that is not part of a three-core directory;
- three-core plans: a directory containing `spec.md`, `plan.md`, and `tasks.md`. Every Markdown file in that directory belongs to the plan and is not reported again as a separate single-file artifact.

Directories named `_archive`, `.git`, `__pycache__`, or `node_modules` are ignored. Run `planvault` to inspect detection and link validation without writing anything:

```bash
python3 tools/codebase-analysis-ai/check.py planvault
python3 tools/codebase-analysis-ai/check.py planvault --strict
```

A repository without `plans/` produces `detected: false` and no errors. `--strict` exits non-zero only for link or map errors, never for the absence of PlanVault.

## Promotion rule

A decision stays in the plan's `Decision Log` while it is tactical, local, reversible, or only meaningful within that plan. Promote it to a decision record when at least one is true:

- it is architectural and shapes components, boundaries, or data ownership;
- it is durable and should outlive the plan;
- it constrains future plans or implementations;
- it changes a public contract, compatibility promise, or migration path;
- it requires an explicit migration or rollback strategy.

Promotion is a parent decision based on evidence. Analyzers may report `decisionCandidates`, but they never create an ADR and never choose the final status. A candidate that is only a recommendation for new code is not an ADR.

## Links between plans and ADRs

A plan may link an ADR, and an ADR may link the plan that confirmed it. Links stay repository-relative and never duplicate the rationale:

- the plan records execution, tasks, status, and the decision log;
- the ADR records context, decision, alternatives, consequences, evidence, and links.

When both artifacts exist, the gate validates that a plan-to-ADR link resolves to an existing file, that the target is registered as `documentKind: decision-record`, and that the ADR lists the plan in `metadata.relatedPlans`. Missing plans, absent PlanVault, or links to anything other than an ADR pattern are not errors.

Register the reverse link in the map, not in the ADR body alone:

```json
{
  "documentKind": "decision-record",
  "metadata": {
    "status": "accepted",
    "date": "2026-01-31",
    "relatedPlans": ["plans/auth-hardening.md"]
  }
}
```

Paths in `relatedPlans` are repository-relative and must exist when validated.

## Update, audit, and ownership

- `update` and `audit` may report an architectural decision that is not yet promoted, but they do not create the ADR and do not modify the plan without explicit user confirmation.
- A completed plan does not change an ADR status by itself. Supersession is a decision made by a new ADR, not by plan completion.
- Documentation workflows never move, rename, renumber, or rewrite PlanVault plans.
- PlanVault never becomes a prerequisite: repositories without it keep valid documentation and valid ADRs.

## Failure modes

- Plan links an ADR that does not exist: reported as a broken link.
- Plan links an existing ADR that is not registered in the documentation map: reported as unregistered.
- ADR does not list the plan in `metadata.relatedPlans`: reported as a missing reverse link.
- No `plans/` directory: no error and no requirement to create one.
