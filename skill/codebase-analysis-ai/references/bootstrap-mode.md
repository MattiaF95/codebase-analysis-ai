# Bootstrap mode

Bootstrap creates documentation from zero and is the only mode allowed to scan the complete repository.

## Preconditions

- Require explicit full-bootstrap intent.
- Confirm the repository root and excluded paths. Exclude agent/runtime metadata and IDE directories (`.agents/`, `.codex/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.vscode/`, `.idea/`, `.zed/`, `.devcontainer/`) from the project documentation inventory.
- Apply `existingDocumentationPolicy: ask`: run the documentation preflight first. If any supported document format or canonical document name exists, stop and ask whether to use `migrate`, update/integrate it incrementally, or explicitly replace it. Do not continue until the user chooses. After the choice, inspect the remaining relevant documents.
- Resolve the documentation language using `document-style.md`. If no reliable policy or canonical documentation exists, ask the user and wait for an answer before generating prose.

## Procedure

1. Inventory tracked source, configuration, tests, deployment, database, and existing Markdown files. Read and integrate the root `README.md` first when present; a user summary of it is not a substitute. Exclude secrets, generated output, agent/IDE metadata, and documentation belonging to installed skills or editor integrations.
2. Detect repository shape using `scripts/codebase_analysis_ai.py detect`.
3. Detect the active host and read only its matching host reference linked from `SKILL.md`.
4. Build the adaptive macro-area list from `project-taxonomy.md`; do not suppress an area merely because the repository is small. If only one area exists, create one analyzer brief for that area.
5. For every macro-area, create or update the host-native project profile described by the host reference. Use a safe slug for the area name and include the managed marker. Never overwrite a file without that marker; treat the collision as an explicit creation failure and use the sequential fallback for that area. Do not create profiles for other hosts or at user scope.
6. Build a self-contained brief for every analyzer with its scope, allowed paths, excluded paths, evidence questions, language constraint, read-only boundary, recursion prohibition, and complete JSON output contract.
7. Refresh or restart host discovery only when required, then attempt native delegation for every brief. Use parallel delegation for independent areas when available; otherwise delegate sequentially. Retry one malformed report once. Fall back to parent-context sequential analysis only after explicit creation, discovery, invocation, timeout, or repeated contract failure, and record the concrete cause.
8. Validate all reports before merging them. Reject claims without allowed-path evidence, merge duplicate cross-area flows, and keep unresolved contradictions under `To verify`.
9. Apply the user's selected existing-documentation strategy: `migrate` rewrites existing files in place, `integrate` carries useful facts from existing files into the new generated structure, and `replace` deletes only the confirmed documentation file list before generating new files. Never delete source code or unconfirmed files.
10. Generate the root `README.md`, `docs/README.md`, macro-area `README.md` files, and topic documents using `document-style.md`.
11. Create `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`.
12. Add direct related-document links and stop relationship traversal at one level.
13. Validate language consistency, human readability, acronym definitions, links, naming, map coverage, source evidence, secret exclusions, generated profile syntax, and the absence of analyzer writes.

Do not leave placeholders unless essential information cannot be derived safely. Mark unresolved facts as `To verify` with the missing evidence.
