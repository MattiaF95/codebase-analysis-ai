# Migrate mode

Migrate restructures existing documentation without performing a general evidence-based content refresh. It may move, rename, index, link, and normalize documents while preserving useful project decisions, explanations, and flows. Use `update` after migration when content must also be synchronized with the implementation.

Migration normally runs in the parent agent because its primary task is indexing and normalizing existing documentation. Reuse existing read-only area profiles only when source ownership, document mapping, or cross-area responsibility cannot be established from the migration inputs. Pass the same self-contained evidence brief and JSON contract used by `update`; validate profile safety and the working tree before and after delegation. Profiles may be invoked in parallel for independent areas, but `migrate` must never create or modify persistent profiles; use the sequential fallback when a profile is unavailable or stale.

## Procedure

1. Read `docs/index.md` first when it exists, then inventory active supported document files and their outbound links. Exclude `docs/_archive/`.
2. Resolve the documentation language before inventory normalization: use repository policy or canonical documents and record the evidence. If evidence is absent or canonical documents conflict, ask the user and wait before selecting a standard language.
3. Detect naming, linking, and structural inconsistencies and prepare the minimum restructuring needed. Do not broadly rewrite technical claims merely to modernize prose.
4. Map existing documents to source files using explicit references, matching component names, and repository evidence.
5. Create stable document IDs and first-level relationships.
6. Generate `docs/_meta/documentation-map.json`, `state.json`, `coverage.md`, and `docs/index.md` when missing, including the language decision. Register the index as `documentation.index`.
7. Apply the selected naming and structure while preserving project decisions, motivations, flows, and other useful facts not present in source code. Restrict prose edits to those required by moves, links, headings, or structural consistency.
8. List every proposed rename, move, deletion, or broad restructuring in the initial contract. Ask again only when the actual operation expands beyond the confirmed set.
9. Update `docs/index.md` for every moved, renamed, added, or removed document. Validate links and report mixed-language documents, readability findings, unmapped documents, and source files.

Do not discard existing documents or unsupported facts merely to match a template. Mark claims that cannot be verified from repository evidence as documented context or unresolved information.
