# Bootstrap mode

Bootstrap creates or completes a documentation system and is the only intent allowed to scan the complete repository. It may include setup, migration, audit, update, generation, and validation phases.

## Preconditions

- Require explicit full-bootstrap intent.
- Confirm the repository root and excluded paths. Exclude agent/runtime metadata and IDE directories (`.agents/`, `.codex/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.vscode/`, `.idea/`, `.zed/`, `.devcontainer/`) from the project documentation inventory.
- Apply `existingDocumentationPolicy: ask`: run the documentation preflight first. If any supported document format or canonical document name exists, stop and ask whether to use `migrate`, update/integrate it incrementally, or explicitly replace it. Do not continue until the user chooses. After the choice, inspect the remaining relevant documents.
- Resolve the documentation language using `document-style.md`. If no reliable policy or canonical documentation exists, ask the user and wait for an answer before generating prose.
- Present the execution contract before delegation: documentation strategy, agent-derived source macro-areas, documentation topics, proposed subagents, parent-only areas, and reasons. Always ask whether to proceed with the delegation proposal, including when proposing no subagents.

## Procedure

1. Run `scripts/codebase_analysis_ai.py detect` to collect a bounded, path-only inventory of root and shallow files, known structural files, possible module roots, extensions, and test/deployment/workflow/migration signals. Root and shallow filenames allow unfamiliar project formats to remain discoverable without adding technology-specific classification rules. Treat every value as evidence to inspect, not as an architectural classification. Exclude secrets, generated output, agent/IDE metadata, and documentation belonging to installed skills or editor integrations.
2. Read and integrate the root `README.md` first when present; a user summary of it is not a substitute. Then read root manifests, workspace/build/deployment files, and only the module manifests or local README files needed to understand the repository. Do not automatically read one file from every directory. Expand the read scope progressively when evidence is ambiguous.
3. Detect the active host and read only its matching host reference linked from `SKILL.md`.
4. The parent agent builds source macro-areas and documentation topics separately using `project-taxonomy.md`. Every area needs evidence-backed candidate paths; detector filenames, extensions, and module-root candidates are never final ownership decisions. Do not suppress useful documentation because the repository is small. A small area may remain parent-only, while a larger independent area may receive one analyzer. Overlapping evidence paths are allowed.
5. For each approved delegated area, create or update the host-native project profile described by the host reference. Use a safe slug and managed marker. Never overwrite an unmanaged collision; record the creation failure and use the parent fallback for that area. Do not create profiles for other hosts or at user scope.
6. Build a self-contained brief for every delegated analyzer with source scope, allowed and excluded paths, documentation facets, evidence questions, language, read-only boundary, recursion prohibition, and complete JSON output contract.
7. Refresh or restart host discovery only when required, then attempt native delegation for every approved brief. Use parallel delegation for independent areas when available. Retry one malformed report once. For each failed area, use parent analysis and record the concrete cause and lost guarantees.
8. Validate all reports before merging them. Reject claims without allowed-path evidence, merge duplicate cross-area flows, map evidence to documentation topics, and keep unresolved contradictions under `To verify`.
9. Apply the selected strategy: `migrate` normalizes existing files in place, `integrate` carries useful facts into the generated structure, and `replace` deletes only the confirmed documentation file list. Never delete source code or unconfirmed files.
10. Present the write report and obtain confirmation when the write set is broader or more destructive than the approved contract.
11. Generate the root `README.md`, `docs/README.md`, evidence-backed topic areas, and only useful macro-area documents using `document-style.md`; do not create empty folders merely for symmetry.
12. Create `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`. Persist the approved taxonomy and area source mappings in the documentation map for reuse by `update` and `audit`, then add direct related-document links with one-level traversal.
13. Validate language consistency, readability, acronym definitions, links, naming, map coverage, source evidence, secret exclusions, profile syntax, and absence of analyzer writes.

Do not leave placeholders unless essential information cannot be derived safely. Mark unresolved facts as `To verify` with the missing evidence.
