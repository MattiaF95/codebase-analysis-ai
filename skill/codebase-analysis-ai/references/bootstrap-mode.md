# Bootstrap mode

Bootstrap creates documentation from zero and is the only mode allowed to scan the complete repository.

## Preconditions

- Require explicit full-bootstrap intent.
- Confirm the repository root and excluded paths.
- Apply `existingDocumentationPolicy: ask`: run the documentation preflight first. If any supported document format or canonical document name exists, stop and ask whether to use `migrate`, update/integrate it incrementally, or explicitly replace it. Do not continue until the user chooses. After the choice, inspect the remaining relevant documents.
- Resolve the documentation language using `document-style.md`. If no reliable policy or canonical documentation exists, ask the user and wait for an answer before generating prose.

## Procedure

1. Inventory tracked source, configuration, tests, deployment, database, and existing Markdown files. Exclude secrets and generated output.
2. Detect repository shape using `scripts/codebase_analysis_ai.py detect`.
3. Divide independent macro-areas among subagents when supported.
4. Require each area analyzer to return the contract in `subagent-contract.md`.
5. Build an adaptive taxonomy from `project-taxonomy.md`; do not create irrelevant areas.
6. Resolve and record the documentation language before drafting any generated document.
7. Apply the user's selected existing-documentation strategy: `migrate` rewrites existing files in place, `integrate` carries useful facts from existing files into the new generated structure, and `replace` deletes only the confirmed documentation file list before generating new files. Never delete source code or unconfirmed files.
8. Generate the root `README.md`, `docs/README.md`, macro-area `README.md` files, and topic documents using `document-style.md`.
9. Create `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`.
10. Add direct related-document links and stop relationship traversal at one level.
11. Validate language consistency, human readability, acronym definitions, links, naming, map coverage, source evidence, and secret exclusions.

Do not leave placeholders unless essential information cannot be derived safely. Mark unresolved facts as `To verify` with the missing evidence.
