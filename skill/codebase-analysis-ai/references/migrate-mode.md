# Migrate mode

Migrate adopts existing documentation without silently rebuilding it.

## Procedure

1. Inventory existing Markdown documents and their outbound links.
2. Detect the dominant documentation language from canonical documents and record the evidence. If canonical documents conflict, ask the user before selecting a standard language.
3. Detect naming, readability, acronym, and structural inconsistencies without rewriting prose.
4. Map existing documents to source files using explicit references, matching component names, and repository evidence.
5. Create stable document IDs and first-level relationships.
6. Generate `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`, including the language decision.
7. Propose structural moves and language normalization separately from metadata creation.
8. Require confirmation before renaming, moving, translating, or broadly rewriting existing documents.
9. Validate links and report mixed-language documents, readability findings, unmapped documents, and source files.

Do not replace existing prose merely to match a template. Normalize content during a later explicit update.
