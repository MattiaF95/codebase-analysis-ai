# Analyzer profile and delegation policy

Apply this shared policy to `bootstrap` and `migrate`. `update` and `audit` are reuse-only modes and must not create or modify persistent analyzer profiles.

## Area and delegation resolution

The parent agent owns the source macro-area decision and the delegation proposal. Resolve the relevant areas before substantive analysis:

- `bootstrap`: derive source macro-areas and documentation topics from structural evidence, then count relevant files after excluding documentation, generated output, dependencies, VCS data, and agent metadata;
- `migrate`: resolve source ownership, document mapping, and cross-area responsibilities from the migration inputs, then count relevant files after applying the same exclusions.

Every area needs evidence-backed candidate paths. Detector filenames, extensions, and module-root candidates are evidence to inspect, not final ownership decisions. Source macro-areas and documentation topics remain separate dimensions; overlapping evidence paths are allowed when the questions differ.

After bounded discovery and before substantive analysis, include exactly one of `parent-only`, `selective`, or `all` in the initial contract, with a brief motivation and per-area assignment when applicable. Include the planned document write set and the host-native paths of any analyzer profiles to be created. Ask for confirmation before delegation, profile creation, or writes. A user-selected delegation policy changes delegation only; it must not reduce documentation scope. An explicit `parent-only` choice suppresses profile creation and analyzer delegation even above the file-count threshold.

When the selected policy is not `parent-only` and at least two independent macro-areas each contain at least 15 relevant files, creating one analyzer profile per such area and delegating those areas are mandatory in `bootstrap` and when `migrate` requires delegated analysis. The threshold must not be replaced by an agent judgment, but an explicit user choice of `parent-only` overrides it. Below the threshold, use `parent-only` unless the user explicitly selects another supported policy. A small or overlapping area may remain parent-only.

## Profile lifecycle

Detect the active host, read exactly one matching host reference linked from `SKILL.md`, and resolve its delegation capability. For every mandatory or explicitly approved delegated area:

1. Create the host-native project profile when it is missing.
2. Reuse an existing managed profile unchanged.
3. Use a safe area slug and the host-specific managed marker.
4. Never overwrite an unmanaged collision; record the creation failure and use the parent fallback for that area.
5. Create profiles only for the active host and at project scope, never at user scope.

Before reuse or invocation, verify the managed marker, host syntax, explicit read-only restrictions, allowed paths, and current macro-area boundaries. Treat missing paths, unresolved placeholders, or changed boundaries as stale. Do not modify an existing profile automatically. Record the concrete cause and use the sequential parent fallback when a profile is stale, unsafe, unavailable, or its creation or invocation fails.

## Invocation and merge

Build a self-contained brief for every delegated analyzer with source scope, allowed and excluded paths, documentation facets, evidence questions, language, read-only boundary, recursion prohibition, and the complete JSON output contract from `subagent-contract.md`. Do not create profiles for inactive hosts or ask analyzers to locate the contract through a relative path.

Refresh or restart host discovery only when required, then attempt native delegation for every approved brief. Use parallel delegation for independent areas when available. Retry one malformed report once. For each failed area, use parent analysis and record the concrete cause and lost guarantees.

Validate all reports before merging them. Reject claims without allowed-path evidence, preserve and merge every `finding`, prioritize critical and high severity findings, merge duplicate cross-area flows, map evidence to documentation topics, and keep unresolved contradictions under `To verify`. If a report contains truncation, inspect the omitted scope or request a continuation before considering the area covered.

The parent remains the orchestrator: it validates reports and source paths, resolves cross-area claims, preserves findings, and alone writes documentation. Capture working-tree state before delegation and verify that analyzers produced no changes after every batch. Never make analyzer delegation recursive.
