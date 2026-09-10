# Bootstrap mode

Bootstrap creates or completes a documentation system and is the only intent allowed to scan the complete repository. It may include setup, migration, audit, update, generation, and validation phases.

## Preconditions

- Require explicit full-bootstrap intent.
- Confirm the repository root and excluded paths. Exclude agent/runtime metadata and IDE directories (`.agents/`, `.codex/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.vscode/`, `.idea/`, `.zed/`, `.devcontainer/`) from the project documentation inventory.
- Apply `existingDocumentationPolicy: ask`: run the documentation preflight first. When documentation exists, propose exactly `archive` or `replace` in the initial contract. Both reuse every useful existing fact in the new documentation. `archive` preserves originals under `docs/_archive/pre-bootstrap/`; `replace` removes superseded originals only after generation and validation. List affected files before confirmation.
- Resolve the documentation language using `document-style.md`. If no reliable policy or canonical documentation exists, include the language choice in the single initial confirmation and wait before substantive analysis or prose generation.
- Present the single initial contract before substantive analysis: ordered phases and final result, language, existing-documentation policy, source macro-areas, documentation topics, one of `parent-only`, `selective`, or `all` with a brief motivation and per-area assignment, planned documents, host-native analyzer profile paths and areas to create, and the adaptive automation proposal. Ask once for confirmation before delegation, installation, or writes.

## Procedure

1. Run `scripts/codebase_analysis_ai.py detect` to collect a bounded, path-only inventory of root and shallow files, known structural files, possible module roots, extensions, and test/deployment/workflow/migration signals. Root and shallow filenames allow unfamiliar project formats to remain discoverable without adding technology-specific classification rules. Treat every value as evidence to inspect, not as an architectural classification. Exclude secrets, generated output, agent/IDE metadata, and documentation belonging to installed skills or editor integrations.
2. Read `docs/index.md` first when it exists, then read and integrate the root `README.md`; a user summary is not a substitute for either canonical file. Read root manifests, workspace/build/deployment files, and only the module manifests or local README files needed to understand the repository. Do not automatically read one file from every directory. Expand progressively when evidence is ambiguous. Ignore `docs/_archive/`.
3. Read `references/analyzer-profile-policy.md` and the active host reference linked from `SKILL.md`, then apply the shared profile and delegation policy.
4. Apply the confirmed policy. For `archive`, copy originals to collision-safe paths below `docs/_archive/pre-bootstrap/` before rewriting or removing them. For `replace`, retain originals until the generated set validates, then remove only the confirmed superseded files. Rewrite canonical files that retain their path in place. Never delete source code or unconfirmed files.
5. Compare the write set with the confirmed contract. Ask again only for a broader, more destructive, or conflicting delta.
6. Generate the root `README.md`, canonical `docs/index.md`, evidence-backed topic areas, and only useful macro-area documents using `document-style.md`; do not create empty folders merely for symmetry. The index must explain the documentation structure and link directly to every top-level active document or area index.
7. Create `docs/_meta/documentation-map.json`, `state.json`, and `coverage.md`. Register `docs/index.md` as `documentation.index` without source patterns or source hashes, persist the approved taxonomy and area source mappings, then add direct related-document links with one-level traversal. Exclude `docs/_archive/` from active metadata.
8. Validate language consistency, readability, acronym definitions, links, naming, map coverage, index completeness, source evidence, archive exclusion, secret exclusions, profile syntax, and absence of analyzer writes.

Do not leave placeholders unless essential information cannot be derived safely. Mark unresolved facts as `To verify` with the missing evidence.
