# Update mode

Update is the default mode for existing Codebase Analysis AI projects.

## Area delegation

After the deterministic checker resolves changed files and impacted documents, map the changed paths to detected macro-areas. When existing host profiles and native delegation are available, invoke exactly one read-only analyzer for each impacted macro-area and run independent areas in parallel. Reuse profiles created during `bootstrap`; never create or modify persistent analyzer profiles during `update`.

Pass each analyzer a self-contained brief containing the narrowed changed paths, allowed and excluded paths, impacted documents, evidence questions, documentation language, read-only boundary, no-recursion rule, and the complete JSON contract from `references/subagent-contract.md`. The analyzer reports evidence and documentation implications only. The parent validates every source path and report, resolves cross-area duplicates, and alone writes documentation.

If a profile is missing, stale, unmanaged, undiscoverable, or invocation fails, record the concrete reason and perform the same area's analysis sequentially in the parent context. Do not skip the area and do not create a replacement profile during `update`. If no documentation is impacted, do not invoke any analyzer.

## Procedure

1. Determine the change source: working tree, staged changes, commit, range, PR, merge, rebase, or pull.
2. Run the deterministic checker to collect changed files and resolve impacted document IDs.
3. Read only changed source files, directly mapped documents, and their first-level related documents.
4. Resolve the documentation language before analyzing impacted prose: read the recorded language from the map, otherwise use only impacted canonical documents; ask the user and wait when they conflict or provide no reliable evidence.
5. Update prose only where behavior or evidence changed, preserving the established language and applying `document-style.md` to changed passages.
6. Expand or explain newly introduced acronyms at their first meaningful use in each impacted document.
7. Scan TODO and FIXME markers only in changed or directly required files.
8. Preserve manual sections and unrelated documents.
9. Update bidirectional links when the relationship is logically bidirectional.
10. Validate the impacted subset for technical accuracy, language consistency, readability, links, and unresolved mappings.
11. After the corresponding document has been reviewed and updated, refresh hashes only for the reviewed changed source paths.
12. Re-run the deterministic checker after refreshing hashes and report any remaining stale mappings.

Never expand from a first-level related document to its own related documents during the same update.
