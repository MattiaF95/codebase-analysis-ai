# Audit mode

Audit is an agent-led, read-only review. It is distinct from the deterministic `check` command.

## Area delegation

For a targeted audit, reuse existing read-only profiles only for user-approved selected source macro-areas and document kinds. For a full audit, reuse one profile for every approved detected area and run independent analyzers in parallel when useful. A small or overlapping area may remain parent-only. Do not create or modify persistent profiles during `audit`. In the initial contract, recommend `parent-only`, `selective`, or `all` with a brief motivation and ask for confirmation even when the proposal is `parent-only`.

Each analyzer receives a self-contained brief with its allowed and excluded paths, audit scope, applicable document kinds and section needs, documentation facets, decision questions, documentation language, evidence questions, read-only/no-recursion rules, and the complete JSON contract. The parent validates reports, preserves and prioritizes `findings`, maps them to document kinds and topics, merges cross-area findings, evaluates decision candidates and ADR supersession gaps, and produces the final read-only audit report. When working parent-only, use the same findings taxonomy and truncation rules. Missing profiles, discovery failures, or malformed reports use the documented sequential fallback and are reported.

For an explicitly full audit, also read `subagent-contract.md`. Reuse existing host profiles when delegation is available; otherwise use the documented sequential parent fallback. Do not create or modify profiles in audit mode.

## Procedure

1. Read `docs/index.md` first, use it to resolve an explicit document scope or the current Git impact set, and report a missing or stale index as a finding. Do not audit `docs/_archive/` unless the user explicitly requests the historical archive.
2. Validate names, document kinds, required sections, links, source references, hashes, ADR status, and mapping consistency. Check that `docs/index.md` links every area index, active kind index, and `_meta/coverage.md`, that coverage counts match the map, and that `docs/_analysis/` and `docs/_archive/` stay out of active navigation. Report documents that lack `documentKind` or `sections` as legacy findings; do not fail them solely for missing optional fields.
3. Resolve the documentation language before reviewing prose: use the recorded decision or canonical documents; ask the user and wait when neither provides reliable evidence, then verify consistency.
4. Review changed or selected documents for understandable context, direct sentences, explicit component names, and explained acronyms using `document-style.md`.
5. Compare documented active behavior with repository evidence.
6. Verify that TODOs and future functionality have explicit sources.
7. Check direct related documents for contradictions and inconsistent terminology.
8. Report findings using the shared `findings` contract: classify each item as `bug`, `security`, `reliability`, `maintainability`, `coverage-gap`, or `documentation`, and use `critical`, `high`, `medium`, `low`, or `info` severity. Include observed behavior, impact, confidence, verification level, recommended action, and evidence. Preserve every critical and high finding and record any lower-severity truncation.
9. Follow `planvault-bridge.md`: when PlanVault plans exist, report architectural decisions that remain only in a plan's decision log and are not promoted to ADRs, and report broken or one-sided plan/ADR links. Do not create ADRs, edit plans, or change ADR status; a completed plan is not evidence that an ADR should change.
10. Do not modify files unless the user changes the request to `update`.

If the user requests a full documentation audit, include the complete-scan boundary in the initial contract before expanding beyond mapped documentation sources.
