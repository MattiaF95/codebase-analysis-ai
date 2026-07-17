---
name: codebase-analysis-ai
description: Analyze repository evidence to bootstrap, migrate, update, or audit project documentation covering architecture, flows, APIs, schemas, security, configuration, and delivery. Use when creating a complete documentation system, synchronizing existing docs with Git or code changes, adopting unmanaged documentation, checking documentation accuracy, or installing the supporting workflow. Prefer bounded Git-diff analysis for updates; use full-repository analysis only for explicit bootstrap requests. Do not use for generic writing, standalone code explanations, or code-quality reviews.
---

# Codebase Analysis AI

Keep repository documentation aligned with implementation changes while minimizing repository reads and repeated analysis.

## Select an intent and execution plan

Start with read-only discovery: resolve the repository and Git state, run `python tools/codebase-analysis-ai/check.py setup-state --agents <active-host>`, inspect documentation presence, and collect only the bounded evidence needed to propose a plan. Do not begin substantive analysis, delegate, install automation, or write files before presenting one initial contract and receiving confirmation. If the setup state is ambiguous or conflicted, describe the conflict in that contract and never overwrite it silently.

After discovery, resolve a primary intent and an ordered execution plan before reading additional references. A plan may combine modes when the context requires it, but must name every phase and briefly explain the expected final result. `bootstrap` may compose setup, structural migration, content update, generation, audit, and validation. `migrate`, `update`, and `audit` remain standalone modes when the repository is already configured. With no explicit mode or clear intent, include the proposed intent in the initial contract and ask the user to confirm it. Interpret requests such as “update the documentation” as `update`.

- `setup`: Install the skill, persistent agent rules, deterministic runtime, Git hooks, or GitHub Action. Require either an explicit setup request or confirmation of a setup phase in the initial contract. Read `references/setup-mode.md` and `references/automation.md`.
- `bootstrap`: Create or complete a documentation system and, when needed, scan the full repository. Require explicit bootstrap intent. Read `references/bootstrap-mode.md`, `references/project-taxonomy.md`, `references/document-style.md`, and `references/subagent-contract.md`. After detecting the active host, read exactly one of `references/host-codex.md`, `references/host-claude.md`, `references/host-gemini.md`, or `references/host-copilot.md`.
- `update`: Update existing documentation from current Git changes, a commit, or a commit range. This is the default synchronization mode. Reuse existing read-only analyzer profiles only for impacted macro-areas. Read `references/update-mode.md`, `references/change-detection.md`, `references/impact-resolution.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is available.
- `audit`: Inspect documentation accuracy, readability, language consistency, and link consistency without changing files. Reuse existing profiles for selected areas or all areas in a full audit. Read `references/audit-mode.md`, `references/quality-rules.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is available.
- `migrate`: Restructure existing documentation without performing a general evidence-based content refresh. It may move, rename, index, link, and normalize documents while preserving their useful content. Use the parent agent by default; reuse area profiles only when source ownership or mapping is ambiguous. Read `references/migrate-mode.md`, `references/documentation-schema.md`, `references/naming-conventions.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is needed.

Do not read references for unrelated modes.

## Existing-documentation policy

`existingDocumentationPolicy: ask` is the default safety policy for `bootstrap` and any request to create documentation from zero. Before generating documents, run `scripts/codebase_analysis_ai.py docs-state` (or perform the equivalent path-only check). If repository documentation exists, include exactly two choices in the initial contract:

- `archive`: use every useful fact from the existing documents in the new documentation, then preserve the originals under `docs/_archive/pre-bootstrap/` using collision-safe repository-relative paths;
- `replace`: use every useful fact from the existing documents in the new documentation, then remove superseded originals only after the new documentation validates successfully.

For a canonical file that remains at the same path, such as the root `README.md`, rewrite it in place; under `archive`, copy its original version to the archive first. List the files to archive, rewrite, and remove before confirmation. Never delete an original before successful generation and validation. Treat `docs/_archive/` as historical material: exclude it from the active documentation map, index, routine updates, audits, and bootstrap inventory.

The setup preflight is read-only and checks common documentation formats plus canonical names such as `README`, `LICENSE`, and `CHANGELOG` without opening arbitrary project files. The documentation check may then inspect only the mapped paths needed for the selected intent. This two-choice policy applies only to bootstrap or initialization; explicit `update`, `audit`, and `migrate` follow their own semantics.

The preflight and bootstrap inventory must exclude agent/runtime metadata and IDE configuration directories, including `.agents/`, `.codex/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.vscode/`, `.idea/`, `.zed/`, and `.devcontainer/`. Documentation shipped inside those directories belongs to the skill, editor, or agent integration, not to the project documentation set. Read `docs/index.md` first when present, then the root `README.md`; both are canonical and must be integrated even if the user already summarized or mentioned them. User-provided context never replaces reading canonical files.

## Resolve language before analysis

After selecting `bootstrap`, `update`, `audit`, or `migrate`, resolve the documentation language before reading repository content beyond what is needed to establish that decision and before drafting or normalizing prose. Use this order:

1. An explicit user choice or repository documentation policy.
2. The dominant language of canonical documentation.
3. If neither provides reliable evidence, ask the user which language to use and wait before continuing.

`setup` does not need a language decision because it only installs tooling and managed instructions. Never infer the language from source-code syntax, identifiers, comments, commit messages, contributor names, locale, or geography. Record the decision in `docs/_meta/documentation-map.json` whenever that metadata file is created or updated.

## Guardrails

1. Never perform a full repository scan unless `bootstrap` is explicit.
2. If `docs/` is missing and bootstrap was not explicit, ask whether to initialize complete documentation or stop.
3. If `docs/` exists but `docs/_meta/documentation-map.json` does not, include the applicable choice in the initial contract: `archive` or `replace` for bootstrap, or standalone `migrate` versus stop for non-bootstrap work. Never silently rebuild all documentation.
4. In `update`, inspect only changed files, mapped documents, and directly related first-level documents. Do not traverse related links recursively.
5. Treat `scripts/codebase_analysis_ai.py check` as a deterministic gate. Treat `audit` as an agent-led read-only review. Do not conflate them.
6. Do not invent commands, architecture, dependencies, active functionality, or planned work. Ground every claim in repository evidence.
7. Never expose secrets, credentials, tokens, certificates, connection strings, or personal data in generated documentation.
8. Write in the repository's established documentation language. For `bootstrap`, `update`, `audit`, or `migrate`, ask the user when no reliable language evidence exists; do not infer language from source code or author location.
9. Preserve technical precision while making prose understandable to an engineer unfamiliar with the repository. Define uncommon or domain-specific acronyms at first use.
10. Preserve manual content outside managed sections.
11. Do not overwrite existing hooks, workflows, or agent instructions without a safe managed-block update. Stop on an unrecognized conflict.
12. Do not commit, push, merge, or enable branch protection unless the user explicitly requests that external action.
13. Create persistent macro-area analyzer profiles only during `bootstrap`, after the parent agent has derived macro-areas from structural evidence and received the user's delegation decision. `setup`, `audit`, `update`, and `migrate` must not create or modify them.
14. Treat source macro-areas and documentation topics as separate dimensions. An analyzer owns an evidence scope; the parent owns the documentation structure. Overlapping evidence paths are allowed when each analyzer has distinct questions.
15. Never make delegation implicit. Propose exactly one of `parent-only`, `selective`, or `all`, give a brief evidence-based motivation, show which areas remain with the parent and which go to analyzers, and ask for confirmation in the initial contract. `selective` is the mixed strategy: delegate large independent areas and keep small, overlapping, or cross-cutting areas in the parent. `all` delegates every safely separable area, but the parent still validates evidence and alone writes documentation.
16. Treat `docs/index.md` as the canonical navigation entry point. Read it first when it exists. Create it during bootstrap, register it in the documentation map, and verify or update it whenever documentation is created, removed, renamed, moved, or materially changes purpose.

## Common execution contract

1. Resolve the repository root and current Git state. Run the setup and documentation preflights. When `docs/index.md` exists, read it before other active documents and use it to navigate only to files required by the selected intent.
2. Resolve the primary intent, proposed phases, existing-documentation strategy, and language. For `bootstrap`, run `detect` to collect bounded, path-only root, shallow, and structural evidence; its output is an inventory, not a project taxonomy.
3. Read the canonical root documentation and only the structural files needed to interpret the inventory. Progressively inspect module manifests or local README files when the initial evidence is insufficient. The parent agent derives source macro-areas, candidate paths, documentation topics, and a delegation proposal; do not treat filenames or extensions as final architectural decisions.
4. Present one initial contract with: the intent and ordered phases; the expected result; language; `archive` or `replace` with exact affected files when bootstrap finds existing documentation; one of the three delegation strategies with a brief motivation and per-area assignment; the planned document write set; and an adaptive automation proposal for agent rules, runtime, every hook, and the GitHub Action. Ask for one confirmation covering the complete contract. If a required user choice is unresolved, include it in the same request. In interactive execution, do not delegate, install, write, archive, or delete before confirmation. In non-interactive execution, require explicit values for every applicable choice, including `delegationPolicy` (`parent-only`, `selective`, or `all`) and `existingDocumentationPolicy` (`archive` or `replace`).
5. Load only the references required for the selected intent and planned phases. Never make the presence of a subagent a prerequisite for creating evidence-based documentation.
6. Detect the active host and its delegation capability. In `bootstrap`, create or safely update one project-level, read-only analyzer profile only for areas approved for delegation. In `update` and `audit`, reuse only existing profiles for impacted or selected areas; do not create persistent profiles. Before reuse, verify the profile's managed marker, host syntax, explicit read-only restrictions, and allowed paths; treat missing paths, unresolved placeholders, or changed area boundaries as stale. Render the area's allowed paths into every invocation brief. Never generate profiles for inactive hosts, write user-level profiles, or overwrite an unmanaged profile. A missing profile during bootstrap triggers a fallback only after the approved delegation plan is recorded.
7. Give every analyzer a self-contained invocation brief containing its source area, allowed paths, excluded paths, evidence questions, documentation facets, language, read-only boundary, recursion prohibition, and complete JSON contract from `references/subagent-contract.md`. Do not rely on a relative reference to the contract from inside a generated profile.
8. The parent remains the orchestrator: it dispatches approved analyzers, collects and validates reports, rejects evidence outside assigned paths, resolves duplicate and cross-area flows, maps reports to documentation topics, and alone writes documentation. Analyzer restrictions prevent writes but do not guarantee path-level isolation; validate returned sources accordingly. Capture working-tree state before delegation and verify it is unchanged after every batch.
9. Run independent approved analyzers in parallel only when the host supports it and wait for the full batch before merging. Do not let analyzers delegate recursively. For every area, require either a valid analyzer report or a recorded parent fallback with a concrete cause and lost guarantees.
10. Before writing, compare the actual write set with the confirmed initial contract. Continue without another confirmation when it stays within that contract. If it becomes broader, more destructive, or introduces a new conflict, stop and ask for a new confirmation describing only the delta.
11. Validate names, links, source mappings, hashes, managed sections, report coverage, and the absence of analyzer writes before completion.
12. Persist the user-approved bootstrap taxonomy and area source mappings in `docs/_meta/documentation-map.json` so later `update` and `audit` runs do not need to reinterpret the whole repository. Register `docs/index.md` as `documentation.index`; keep it outside source-impact fan-out and update it when the active documentation set or its navigation changes.
13. Report the requested intent, executed phases, delegation decision, profiles created or reused, fallbacks, changed documentation, checked relationships, unresolved evidence, and validation results. Do not delete stale managed profiles automatically; report them for explicit cleanup.

## Deterministic entry point

Use `scripts/codebase_analysis_ai.py` for documentation preflight, bounded structural inventory, change collection, impact resolution, hash checks, link validation, project setup, and metadata refresh. The `detect` command never determines architecture, technologies, macro-areas, or documentation topics. Run `python scripts/codebase_analysis_ai.py --help` for available commands.
