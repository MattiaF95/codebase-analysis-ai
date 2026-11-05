# Subagent contract

Use `references/analyzer-profile-policy.md` for profile creation, reuse, delegation, validation, and fallback in `bootstrap` and `migrate`. During `bootstrap`, use one independent analyzer per approved, delegable source macro-area; during `update`, reuse one existing analyzer for each approved impacted macro-area; during a targeted `audit`, reuse one for each approved selected area; during a full `audit`, reuse one for every approved detected area; and during `migrate`, use one for each area requiring delegated ownership or mapping analysis. A small or overlapping area may remain parent-only. Analyzer execution remains read-only; profile creation is a parent orchestration action governed by the shared policy and is not allowed in `update` or `audit`.

## Reuse and safety checks

The parent invokes profiles through the active host's native mechanism; this contract does not assume a host-neutral dispatcher. Before invocation, verify the host capability, managed marker, valid host syntax, explicit read-only tool restrictions, resolved allowed paths, and current macro-area boundaries. Treat an unavailable capability or failed check as a fallback condition and use the sequential parent fallback without editing the profile. A native call that reaches the host's bounded deadline without a valid result is also a fallback condition. Capture the working-tree status before delegation and compare it after the batch; any analyzer-created change is a read-only violation and must stop the batch.

## Invocation brief

The parent must pass the complete brief directly to each analyzer. Allowed paths come from a user-approved, parent-derived taxonomy or migration area mapping, persisted during bootstrap when available, never directly from detector output. Include:

- `area`, allowed repository-relative paths, and excluded paths;
- evidence questions, documentation facets, and the already resolved documentation language;
- the document kinds in scope, their required and recommended section keys, and whether decision discovery is in scope;
- read-only and no-recursion rules;
- the complete output schema below.

Never ask an analyzer to locate this contract through a relative path. Exclude secrets, credentials, generated output, dependency directories, VCS internals, and host metadata unless a specific metadata file is itself the evidence under review.

## Output schema

Return JSON only. Every documentation claim must carry repository evidence.

```json
{
  "area": "backend",
  "paths": ["backend/src"],
  "technologies": [{"name": "Spring Boot", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "responsibilities": [{"description": "Expose REST APIs", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "entryPoints": [{"path": "...", "purpose": "...", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "dependencies": {
    "internal": [{"name": "shared-auth", "purpose": "Authorize requests", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
    "external": [{"name": "PostgreSQL", "purpose": "Persist application data", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}]
  },
  "flows": [{"name": "Authentication", "description": "Validate a bearer token", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "security": [{"description": "Administrative endpoints require an admin role", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "terminology": [{"term": "RBAC", "definition": "Role-Based Access Control", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "activeFunctionality": [{"description": "Create and retrieve records", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "todos": [{"path": "...", "line": 1, "text": "..."}],
  "documentationNeeded": [{
    "topic": "Authentication",
    "documentKind": "topic",
    "sectionNeeds": ["context", "how-it-works"],
    "reason": "The flow crosses multiple components",
    "sources": [{"path": "...", "line": 1, "symbol": "..."}]
  }],
  "decisionCandidates": [{
    "title": "Use short-lived signed sessions",
    "category": "security",
    "proposedStatus": "accepted",
    "context": "Session validation is duplicated across services",
    "decision": "Centralize session validation in the shared auth module",
    "alternatives": ["Keep per-service validation", "Use opaque database sessions"],
    "consequences": ["One signing key must be rotated centrally", "Services lose independent session formats"],
    "supersedes": ["ADR-0002"],
    "relatedPlans": ["plans/auth-hardening.md"],
    "sources": [{"path": "...", "line": 1, "symbol": "..."}],
    "confidence": "high",
    "confidenceReason": "The shared module and all callers were inspected"
  }],
  "findings": [{
    "kind": "documentation",
    "severity": "high",
    "description": "The README documents an endpoint that is absent from the controller",
    "observedBehavior": "The documented endpoint has no matching controller route",
    "impact": "Users may follow an invalid API contract",
    "confidence": "high",
    "confidenceReason": "The README and complete controller were inspected",
    "verification": "source-only",
    "recommendedAction": "Update the README or restore the endpoint after confirming the intended contract",
    "affectedPaths": ["README.md", "src/api/controller.py"],
    "sources": [{"path": "README.md", "line": 42}, {"path": "src/api/controller.py", "line": 18}]
  }],
  "uncertainties": [{"question": "...", "missingEvidence": "..."}],
  "truncation": [],
  "confidence": 0.9
}
```

Each `sources` array for a reported claim must contain at least one object with a repository-relative `path`, a one-based `line` when available, and an optional `symbol`. Findings may cite up to five representative sources when the inconsistency crosses multiple files. Use an empty result array instead of unsupported claims.

## Decision candidates

`decisionCandidates` is optional and may be empty. A candidate records a decision that the evidence already shows, not a recommendation for new code. Report the title, category, context, decision, alternatives, consequences, optional `supersedes`/`relatedPlans`, evidence sources, and confidence. `proposedStatus` is a hint only: the parent decides the final ADR status and alone writes or updates the decision record. Tactical or reversible choices remain in the plan's decision log when PlanVault is used, or in implementation notes; do not inflate them into ADRs.

Keep the report bounded and documentation-oriented: group closely related findings, return at most 24 items in ordinary arrays, at most 40 TODOs, and at most 40 `findings` per report. Do not enumerate every function or file when one responsibility or flow explains them. Findings must use exactly one kind (`bug`, `security`, `reliability`, `maintainability`, `coverage-gap`, or `documentation`) and one severity (`critical`, `high`, `medium`, `low`, or `info`). Every finding must include `description`, `observedBehavior`, `impact`, `confidence` (`high`, `medium`, or `low`), `confidenceReason`, `verification` (`source-only`, `test`, `runtime`, or `external-state`), `recommendedAction`, `affectedPaths`, and evidence-backed `sources`. Severity describes impact and must not be used as confidence. Report every `critical` and `high` finding; if the findings exceed the report budget, put only lower-severity findings in `truncation`. When any relevant result is omitted, add `{\"section\": \"...\", \"omitted\": 1, \"reason\": \"report limit\", \"nextAction\": \"request continuation or inspect the omitted scope in the parent\"}` to `truncation`.

The `findings` section is mandatory in shape even when it is empty. An empty array means that the assigned scope produced no supported finding in the shared taxonomy; it does not mean that the scope was not inspected.

The parent must preserve, validate, prioritize, and merge `findings` before writing documentation. When delegation is unavailable, the parent uses the same taxonomy, severity rules, source requirements, and truncation handling for its own analysis. Findings must never be silently discarded because the parent is working alone.

## Analyzer rules

- Read only the assigned allowed paths and never write, edit, execute mutating commands, or propose code fixes.
- Do not spawn or invoke other agents. Do not choose a documentation language or writing style.
- Report uncertainty instead of inferring behavior that the repository does not prove.
- Report documentation kind needs and decision candidates; do not create or modify documentation, ADRs, or plans.

## Parent validation and merge

Reject a report when it is not valid JSON, names the wrong area, cites paths outside the allowed scope, or provides claims without sources. Retry one malformed report once; after a second failure, record the native invocation failure and perform the same analysis sequentially in the parent.

The parent resolves duplicate flows and terminology, validates every proposed `documentKind` against the applicable catalog, maps evidence to document kinds and topics, validates decision candidates, and alone writes documentation and decision records. The parent decides ADR status, supersession, and PlanVault links; analyzers only report candidates. Do not pass one analyzer's conclusions to another. Initial absence of a profile is a fallback only after the user-approved delegation plan is recorded and the applicable profile creation attempt fails. In `bootstrap` and `migrate`, missing profiles must be created when required by the shared policy; in `update` and `audit`, missing or stale profiles are explicit fallback reasons and must be reported.

## Delegation decision

Use exactly three user-facing policies:

- `parent-only`: the parent analyzes every area; prefer it for small repositories or highly overlapping evidence.
- `selective`: the parent keeps small, cross-cutting, or overlapping areas and delegates large independent areas. This is the only mixed policy.
- `all`: delegate every safely separable area; the parent still validates, merges, resolves cross-area claims, and writes documentation.

After bounded read-only discovery and before substantive analysis, recommend one policy with a brief motivation based on area size, independence, overlap, host capability, and expected context cost. Show a per-area assignment for `selective` or `all`, list the host-native paths of profiles planned for creation, then include the choice in the single initial confirmation. Do not use `recommended` as a policy name. A user-selected policy changes delegation only; it must not reduce documentation scope. An explicit `parent-only` choice suppresses profile creation and analyzer delegation even above the file-count threshold.
