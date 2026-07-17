# Subagent contract

Use one independent analyzer per approved, delegable source macro-area during `bootstrap`. During `update`, use one existing analyzer for each approved impacted macro-area; during a targeted `audit`, use one for each approved selected area; during a full `audit`, use one for every approved detected area. `migrate` may use existing profiles only for unresolved source ownership or cross-area mapping. A small or overlapping area may remain parent-only. All modes must remain read-only for analyzers and must not create agent files outside `bootstrap`.

## Reuse and safety checks

The parent invokes profiles through the active host's native mechanism; this contract does not assume a host-neutral dispatcher. Before invocation, verify the managed marker, valid host syntax, explicit read-only tool restrictions, resolved allowed paths, and current macro-area boundaries. Treat a failed check as a stale profile and use the sequential parent fallback without editing the profile. Capture the working-tree status before delegation and compare it after the batch; any analyzer-created change is a read-only violation and must stop the batch.

## Invocation brief

The parent must pass the complete brief directly to each analyzer. Allowed paths come from the user-approved, agent-derived taxonomy persisted during bootstrap, never directly from detector output. Include:

- `area`, allowed repository-relative paths, and excluded paths;
- evidence questions, documentation facets, and the already resolved documentation language;
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
  "documentationNeeded": [{"topic": "Authentication", "reason": "The flow crosses multiple components", "sources": [{"path": "...", "line": 1, "symbol": "..."}]}],
  "uncertainties": [{"question": "...", "missingEvidence": "..."}],
  "truncation": [],
  "confidence": 0.9
}
```

Each `sources` array for a reported claim must contain at least one object with a repository-relative `path`, a one-based `line` when available, and an optional `symbol`. Use an empty result array instead of unsupported claims.

Keep the report bounded and documentation-oriented: group closely related findings, return at most 12 items per array, at most 20 TODOs, and at most three representative sources per claim. Do not enumerate every function or file when one responsibility or flow explains them. When a limit omits relevant findings, add `{"section": "...", "omitted": 1, "reason": "contract limit"}` to `truncation`.

## Analyzer rules

- Read only the assigned allowed paths and never write, edit, execute mutating commands, or propose code fixes.
- Do not spawn or invoke other agents. Do not choose a documentation language or writing style.
- Report uncertainty instead of inferring behavior that the repository does not prove.

## Parent validation and merge

Reject a report when it is not valid JSON, names the wrong area, cites paths outside the allowed scope, or provides claims without sources. Retry one malformed report once; after a second failure, record the native invocation failure and perform the same analysis sequentially in the parent.

The parent resolves duplicate flows and terminology, maps evidence to documentation topics, validates cross-area claims against all relevant areas, and alone writes documentation. Do not pass one analyzer's conclusions to another. Initial absence of a profile is a fallback only after the user-approved delegation plan is recorded and profile creation fails. In later modes, missing or stale profiles are explicit fallback reasons and must be reported.

## Delegation decision

In interactive execution, the parent must always report one of `parent-only`, `selective`, `recommended`, or `all`, explain the decision using area size, independence, overlap, host capability, and expected context cost, and ask whether to proceed. This confirmation is required even when the parent recommends no subagent. A refusal changes delegation only; it must not reduce the documentation scope.
