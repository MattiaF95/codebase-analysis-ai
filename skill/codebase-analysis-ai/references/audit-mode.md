# Audit mode

Audit is an agent-led, read-only review. It is distinct from the deterministic `check` command.

## Area delegation

For a targeted audit, reuse existing read-only profiles only for user-approved selected source macro-areas. For a full audit, reuse one profile for every approved detected area and run independent analyzers in parallel when useful. A small or overlapping area may remain parent-only. Do not create or modify persistent profiles during `audit`. In the initial contract, recommend `parent-only`, `selective`, or `all` with a brief motivation and ask for confirmation even when the proposal is `parent-only`.

Each analyzer receives a self-contained brief with its allowed and excluded paths, audit scope, documentation facets, documentation language, evidence questions, read-only/no-recursion rules, and the complete JSON contract. The parent validates reports, preserves and prioritizes `findings`, maps them to documentation topics, merges cross-area findings, and produces the final read-only audit report. When working parent-only, use the same findings taxonomy and truncation rules. Missing profiles, discovery failures, or malformed reports use the documented sequential fallback and are reported.

For an explicitly full audit, also read `subagent-contract.md`. Use existing host profiles or temporary runtime workers when delegation is available, but do not create or modify persistent profiles in audit mode.

## Procedure

1. Read `docs/index.md` first, use it to resolve an explicit document scope or the current Git impact set, and report a missing or stale index as a finding. Do not audit `docs/_archive/` unless the user explicitly requests the historical archive.
2. Validate names, required sections, links, source references, hashes, and mapping consistency.
3. Resolve the documentation language before reviewing prose: use the recorded decision or canonical documents; ask the user and wait when neither provides reliable evidence, then verify consistency.
4. Review changed or selected documents for understandable context, direct sentences, explicit component names, and explained acronyms using `document-style.md`.
5. Compare documented active behavior with repository evidence.
6. Verify that TODOs and future functionality have explicit sources.
7. Check direct related documents for contradictions and inconsistent terminology.
8. Report findings using the shared `findings` contract: classify each item as `error`, `inconsistency`, `risk`, or `missing_documentation`, and use `critical`, `high`, `medium`, or `low` severity. Preserve every critical and high finding and record any lower-severity truncation.
9. Do not modify files unless the user changes the request to `update`.

If the user requests a full documentation audit, include the complete-scan boundary in the initial contract before expanding beyond mapped documentation sources.
