# Update mode

Update is the default mode for existing Codebase Analysis AI projects.

## Procedure

1. Determine the change source: working tree, staged changes, commit, range, PR, merge, rebase, or pull.
2. Run the deterministic checker to collect changed files and resolve impacted document IDs.
3. Read only changed source files, directly mapped documents, and their first-level related documents.
4. Read the recorded documentation language from the map. If it is missing, infer it only from the impacted canonical documents; ask the user when those documents conflict or provide no reliable evidence.
5. Update prose only where behavior or evidence changed, preserving the established language and applying `document-style.md` to changed passages.
6. Expand or explain newly introduced acronyms at their first meaningful use in each impacted document.
7. Scan TODO and FIXME markers only in changed or directly required files.
8. Preserve manual sections and unrelated documents.
9. Update bidirectional links when the relationship is logically bidirectional.
10. Refresh hashes only after the corresponding document has been reviewed and updated.
11. Validate the impacted subset for technical accuracy, language consistency, readability, links, and unresolved mappings.

Never expand from a first-level related document to its own related documents during the same update.
