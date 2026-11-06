# Decision records

Decision records preserve durable architectural rationale. They are not a changelog, a task list, or a copy of an execution plan.

## When a decision becomes an ADR

Create an ADR when a decision is architectural, durable, constrains future plans or implementations, changes a public contract, or requires a migration. Keep tactical, local, or reversible choices in implementation notes or in a PlanVault plan's decision log. The parent agent owns promotion; analyzers only report decision candidates.

## Location and naming

- Canonical location: `docs/decisions/ADR-NNNN-<slug>.md`.
- `docs/adr/` is a recognized legacy alias. Existing ADRs keep their path, filename, and number; never rename or renumber them automatically.
- The number is exactly four digits, unique in the repository, and must match the filename and the `ADR-NNNN:` title prefix.
- The slug is lowercase `kebab-case`.

## Required content and map registration

Copy `assets/templates/adr.md` and localize the prose and headings without changing the canonical filename. Every ADR is registered in `docs/_meta/documentation-map.json` with:

```json
{
  "documentKind": "decision-record",
  "sections": {
    "context": "Context",
    "decision": "Decision",
    "alternatives": "Alternatives considered",
    "consequences": "Consequences",
    "evidence": "Evidence",
    "links": "Links"
  },
  "sourcePatterns": [],
  "sourceHashes": {},
  "metadata": {
    "status": "accepted",
    "date": "2026-01-31",
    "supersedes": [],
    "supersededBy": null,
    "relatedPlans": []
  }
}
```

`sourcePatterns` and `sourceHashes` stay empty: an ADR is not a living source-mapped document, and update/audit must never refresh its hashes. `metadata.status` is one of `proposed`, `accepted`, `rejected`, `superseded`, or `deprecated`. `metadata.date` uses `YYYY-MM-DD`. `supersedes` accepts a record ID, filename, `ADR-NNNN`, or four-digit number; `supersededBy` accepts one reference. `relatedPlans` is optional and lists repository-relative plan paths.

## Lifecycle

- `proposed`: the decision is under review. The rationale may still be clarified.
- `accepted`: the rationale is immutable. Change only the status or supersession links when a new decision replaces it; never rewrite its context, decision, alternatives, consequences, or evidence.
- `rejected` and `deprecated`: terminal states for a decision that was not adopted or is no longer recommended.
- `superseded`: requires `metadata.supersededBy` pointing to the newer ADR, and the newer ADR must list the old one in `metadata.supersedes`. The newer ADR must be `accepted`, `proposed`, or itself `superseded`, so chains such as ADR-0001 → ADR-0002 → ADR-0003 are valid.

A new decision that replaces an accepted one creates a new ADR; it does not edit the old rationale. The old ADR becomes `superseded` and both directions are recorded. A completed plan does not change an ADR's status by itself.

## Index and validation

`docs/decisions/index.md` is the kind index. Copy `assets/templates/decisions-index.md`, group records by status, give every record a one-line summary and a relative link, and link the index from `docs/index.md`. `docs/adr/index.md` remains acceptable for a legacy directory.

The deterministic gate validates the filename and number, status, date, required sections, title number, empty source mappings, index presence, valid links, related-plan existence, and supersession consistency. It never rewrites prose or hashes. `--warn-only` keeps every new ADR error non-blocking and `--json` remains machine-readable.

## Migration

When registering existing ADRs, preserve their files and numbers. Add the missing `documentKind`, localized `sections`, and `metadata` in the map, and link them from the applicable index. If an existing ADR lives under `docs/adr/`, keep it there and use `docs/adr/index.md` when that index exists; otherwise link it from `docs/decisions/index.md`. Do not migrate content, rename files, or renumber records unless the user explicitly requests it.
