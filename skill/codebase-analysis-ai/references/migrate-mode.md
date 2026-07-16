# Migrate mode

Migrate adopts existing documentation and rewrites it in place according to the selected documentation style without silently deleting it.

## Procedure

1. Inventory existing supported document files and their outbound links where the format is readable.
2. Resolve the documentation language before inventory normalization: use repository policy or canonical documents and record the evidence. If evidence is absent or canonical documents conflict, ask the user and wait before selecting a standard language.
3. Detect naming, readability, acronym, and structural inconsistencies and prepare an in-place rewrite that preserves useful existing information.
4. Map existing documents to source files using explicit references, matching component names, and repository evidence.
5. Create stable document IDs and first-level relationships.
6. Generate `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`, including the language decision.
7. Apply the selected style and language to the mapped documents while preserving project decisions, motivations, flows, and other useful facts not present in source code.
8. Require confirmation before renaming, moving, deleting, or broadly restructuring existing documents.
9. Validate links and report mixed-language documents, readability findings, unmapped documents, and source files.

Do not discard existing documents or unsupported facts merely to match a template. Mark claims that cannot be verified from repository evidence as documented context or unresolved information.
