# Update mode

Update is the default mode for existing Codebase Analysis AI projects.

## Area delegation

After the deterministic checker resolves changed files and impacted documents, map the changed paths to source macro-areas, documentation kinds, and documentation topics. Reuse existing profiles only for user-approved impacted areas and run independent areas in parallel when useful. Reuse profiles created during `bootstrap` or `migrate`; never create or modify persistent analyzer profiles during `update`. In the initial contract, recommend `parent-only`, `selective`, or `all` with a brief motivation and ask for confirmation even when the proposal is `parent-only`.

Pass each analyzer a self-contained brief containing the narrowed changed paths, allowed and excluded paths, impacted documents, applicable document kinds and section needs, documentation facets, decision questions, evidence questions, documentation language, read-only boundary, no-recursion rule, and the complete JSON contract from `references/subagent-contract.md`. The analyzer reports evidence, findings, documentation implications, and decision candidates only. The parent validates every source path and report, preserves and prioritizes `findings`, resolves cross-area duplicates, maps evidence to document kinds and topics, decides ADR promotion, and alone writes documentation and decision records. Apply the same findings taxonomy and truncation rules when no analyzer is invoked.

If a profile is missing, stale, unmanaged, undiscoverable, native delegation is unavailable, invocation times out, or invocation fails, record the concrete reason and perform the same area's analysis sequentially in the parent context. Do not skip the area and do not create a replacement profile during `update`. If no documentation is impacted, do not invoke any analyzer.

## Procedure

1. Determine the change source: working tree, staged changes, commit, range, PR, merge, rebase, or pull.
2. Run the deterministic checker to collect changed files and resolve impacted document IDs.
3. Read `docs/index.md` first, then only changed source files, directly mapped documents, and their first-level related documents. Do not use the index to expand into unrelated documents.
4. Resolve the documentation language before analyzing impacted prose: read the recorded language from the map, otherwise use only impacted canonical documents; ask the user and wait when they conflict or provide no reliable evidence.
5. Update prose only where behavior or evidence changed, preserving the established language and applying `document-style.md` to changed passages.
6. Expand or explain newly introduced acronyms at their first meaningful use in each impacted document.
7. Scan TODO and FIXME markers only in changed or directly required files.
8. Preserve manual sections and unrelated documents.
9. Update bidirectional links when the relationship is logically bidirectional.
10. Validate the impacted subset for technical accuracy, language consistency, readability, links, and unresolved mappings.
11. Verify `docs/index.md` on every documentation update. Modify it when documents are added, removed, renamed, moved, or their purpose/navigation description becomes stale, and keep every area index and active kind index linked. Keep `docs/_meta/coverage.md` consistent with the map through the `coverage` command; never list `docs/_analysis/` or `docs/_archive/` as active documentation.
12. After the corresponding document has been reviewed and updated, refresh hashes only for the reviewed changed source paths. Never refresh hashes for decision records, whose `sourceHashes` stay empty.
13. Re-run the deterministic checker after refreshing hashes and report any remaining stale mappings, kind, section, ADR, navigation, coverage, or PlanVault link errors.
14. Follow `planvault-bridge.md`: report architectural decisions that are not yet promoted to ADRs, but do not create an ADR or modify a plan without explicit confirmation. A completed plan does not change an ADR status. When a plan and an ADR link each other, keep the plan-to-ADR link and the ADR `metadata.relatedPlans` entry consistent.

Never expand from a first-level related document to its own related documents during the same update.
