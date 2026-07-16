# Audit mode

Audit is an agent-led, read-only review. It is distinct from the deterministic `check` command.

For an explicitly full audit, also read `subagent-contract.md`. Use existing host profiles or temporary runtime workers when delegation is available, but do not create or modify persistent profiles in audit mode.

## Procedure

1. Resolve an explicit document scope or use the current Git impact set.
2. Validate names, required sections, links, source references, hashes, and mapping consistency.
3. Resolve the documentation language before reviewing prose: use the recorded decision or canonical documents; ask the user and wait when neither provides reliable evidence, then verify consistency.
4. Review changed or selected documents for understandable context, direct sentences, explicit component names, and explained acronyms using `document-style.md`.
5. Compare documented active behavior with repository evidence.
6. Verify that TODOs and future functionality have explicit sources.
7. Check direct related documents for contradictions and inconsistent terminology.
8. Report findings by severity: blocking, stale, incomplete, and advisory.
9. Do not modify files unless the user changes the request to `update`.

If the user requests a full documentation audit, confirm whether a complete repository scan is intended before expanding beyond mapped documentation sources.
