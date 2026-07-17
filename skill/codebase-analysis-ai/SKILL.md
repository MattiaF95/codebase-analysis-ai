---
name: codebase-analysis-ai
description: Perform agentic, evidence-based codebase analysis to create, update, migrate, or audit repository documentation covering architecture, code flows, APIs, schemas, security boundaries, configuration, and delivery pipelines. Use after code, configuration, commit, PR, merge, rebase, or pull changes when documentation may need synchronization, or when an explicit documentation review is requested. Default to Git-diff-based incremental analysis and inspect only directly impacted documents and their first-level links. Never scan the entire repository or create documentation from scratch unless the user explicitly requests a full documentation bootstrap. If documentation is missing and bootstrap was not explicit, ask whether to initialize it or stop. Do not use for generic writing, standalone code explanation, or a general code-quality review unrelated to documentation.
---

# Codebase Analysis AI

Keep repository documentation aligned with implementation changes while minimizing repository reads and repeated analysis.

## Select an intent and execution plan

Run `python tools/codebase-analysis-ai/check.py setup-state --agents <active-host>` before selecting an intent. If the plan requires host delegation and the runtime or active-host adapter is absent, stop and ask to run `setup`; a confirmed `parent-only` plan may continue without them. If hooks or the GitHub Action are absent, report them as optional and ask separately whether to install them; if already present, continue without asking. If the setup state is ambiguous or conflicted, do not overwrite anything and ask the user.

After the preflight, resolve a primary intent and an execution plan before reading additional references. `bootstrap` may compose `setup`, `migrate`, `audit`, `update`, analysis, generation, and validation phases. `migrate`, `update`, and `audit` remain standalone modes when the repository is already configured. With no explicit mode or clear intent, ask the user which intent to use. Interpret requests such as “update the documentation” as `update`.

- `setup`: Install the skill, persistent agent rules, deterministic runtime, Git hooks, or GitHub Action. Require an explicit setup request. Read `references/setup-mode.md` and `references/automation.md`.
- `bootstrap`: Create or complete a documentation system and, when needed, scan the full repository. Require explicit bootstrap intent. Read `references/bootstrap-mode.md`, `references/project-taxonomy.md`, `references/document-style.md`, and `references/subagent-contract.md`. After detecting the active host, read exactly one of `references/host-codex.md`, `references/host-claude.md`, `references/host-gemini.md`, or `references/host-copilot.md`.
- `update`: Update existing documentation from current Git changes, a commit, or a commit range. This is the default synchronization mode. Reuse existing read-only analyzer profiles only for impacted macro-areas. Read `references/update-mode.md`, `references/change-detection.md`, `references/impact-resolution.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is available.
- `audit`: Inspect documentation accuracy, readability, language consistency, and link consistency without changing files. Reuse existing profiles for selected areas or all areas in a full audit. Read `references/audit-mode.md`, `references/quality-rules.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is available.
- `migrate`: Index and normalize existing documentation that has no Codebase Analysis AI metadata. Use the parent agent by default; reuse area profiles only when source-to-document mapping or ownership is ambiguous. Read `references/migrate-mode.md`, `references/documentation-schema.md`, `references/naming-conventions.md`, `references/document-style.md`, and `references/subagent-contract.md` when delegation is needed.

Do not read references for unrelated modes.

## Existing-documentation policy

`existingDocumentationPolicy: ask` is the default safety policy for `bootstrap` and any request to create documentation from zero. Before generating documents, run `scripts/codebase_analysis_ai.py docs-state` (or perform the equivalent path-only check). If any existing repository documentation is present, stop and ask the user whether to:

- adopt and index it with `migrate`;
- update or integrate it incrementally; or
- explicitly replace it with a new bootstrap.

The setup preflight is read-only and checks common documentation formats plus canonical names such as `README`, `LICENSE`, and `CHANGELOG` without opening arbitrary project files. The documentation check may then inspect only the mapped paths needed for the selected intent. `existingDocumentationPolicy: ask` is a bootstrap or initialization gate; explicit `update`, `audit`, and `migrate` follow their own documented semantics without asking to choose a different strategy.

The preflight and bootstrap inventory must exclude agent/runtime metadata and IDE configuration directories, including `.agents/`, `.codex/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.vscode/`, `.idea/`, `.zed/`, and `.devcontainer/`. Documentation shipped inside those directories belongs to the skill, editor, or agent integration, not to the project documentation set. The root `README.md`, when present, is the first canonical project document to read and must be integrated even if the user already summarized or mentioned it; user-provided context never replaces reading the canonical file.

## Resolve language before analysis

After selecting `bootstrap`, `update`, `audit`, or `migrate`, resolve the documentation language before reading repository content beyond what is needed to establish that decision and before drafting or normalizing prose. Use this order:

1. An explicit user choice or repository documentation policy.
2. The dominant language of canonical documentation.
3. If neither provides reliable evidence, ask the user which language to use and wait before continuing.

`setup` does not need a language decision because it only installs tooling and managed instructions. Never infer the language from source-code syntax, identifiers, comments, commit messages, contributor names, locale, or geography. Record the decision in `docs/_meta/documentation-map.json` whenever that metadata file is created or updated.

## Guardrails

1. Never perform a full repository scan unless `bootstrap` is explicit.
2. If `docs/` is missing and bootstrap was not explicit, ask whether to initialize complete documentation or stop.
3. If `docs/` exists but `docs/_meta/documentation-map.json` does not, ask which existing-documentation path to use; after the user selects `migrate`, do not silently rebuild all documentation.
4. In `update`, inspect only changed files, mapped documents, and directly related first-level documents. Do not traverse related links recursively.
5. Treat `scripts/codebase_analysis_ai.py check` as a deterministic gate. Treat `audit` as an agent-led read-only review. Do not conflate them.
6. Do not invent commands, architecture, dependencies, active functionality, or planned work. Ground every claim in repository evidence.
7. Never expose secrets, credentials, tokens, certificates, connection strings, or personal data in generated documentation.
8. Write in the repository's established documentation language. For `bootstrap`, `update`, `audit`, or `migrate`, ask the user when no reliable language evidence exists; do not infer language from source code or author location.
9. Preserve technical precision while making prose understandable to an engineer unfamiliar with the repository. Define uncommon or domain-specific acronyms at first use.
10. Preserve manual content outside managed sections.
11. Do not overwrite existing hooks, workflows, or agent instructions without a safe managed-block update. Stop on an unrecognized conflict.
12. Do not commit, push, merge, or enable branch protection unless the user explicitly requests that external action.
13. Create persistent macro-area analyzer profiles only during `bootstrap`, after detecting the macro-areas and receiving the user's delegation decision. `setup`, `audit`, `update`, and `migrate` must not create or modify them.
14. Treat source macro-areas and documentation topics as separate dimensions. An analyzer owns an evidence scope; the parent owns the documentation structure. Overlapping evidence paths are allowed when each analyzer has distinct questions.
15. Never make delegation implicit in interactive execution. The parent must report whether it proposes `parent-only`, `selective`, `recommended`, or `all` delegation, explain why, and ask whether to proceed. If the parent proposes no subagent, it must still ask whether the user wants one.

## Common execution contract

1. Resolve the repository root and current Git state.
2. Resolve the primary intent, existing-documentation strategy, language, source macro-areas, documentation topics, and delegation proposal.
3. Present one pre-analysis contract and ask for confirmation. In interactive execution, do not create or invoke new subagents before the user confirms the delegation proposal. In non-interactive execution, require an explicit `delegationPolicy` such as `parent-only`, `recommended`, or `all`.
4. Load only the references required for the selected intent and planned phases.
5. Run deterministic scripts before agent analysis whenever possible. Detect source macro-areas and separately derive documentation topics; never make the presence of a subagent a prerequisite for creating evidence-based documentation.
6. Detect the active host and its delegation capability. In `bootstrap`, create or safely update one project-level, read-only analyzer profile only for areas approved for delegation. In `update` and `audit`, reuse only existing profiles for impacted or selected areas; do not create persistent profiles. Before reuse, verify the profile's managed marker, host syntax, explicit read-only restrictions, and allowed paths; treat missing paths, unresolved placeholders, or changed area boundaries as stale. Render the area's allowed paths into every invocation brief. Never generate profiles for inactive hosts, write user-level profiles, or overwrite an unmanaged profile. A missing profile during bootstrap triggers a fallback only after the approved delegation plan is recorded.
7. Give every analyzer a self-contained invocation brief containing its source area, allowed paths, excluded paths, evidence questions, documentation facets, language, read-only boundary, recursion prohibition, and complete JSON contract from `references/subagent-contract.md`. Do not rely on a relative reference to the contract from inside a generated profile.
8. The parent remains the orchestrator: it dispatches approved analyzers, collects and validates reports, rejects evidence outside assigned paths, resolves duplicate and cross-area flows, maps reports to documentation topics, and alone writes documentation. Analyzer restrictions prevent writes but do not guarantee path-level isolation; validate returned sources accordingly. Capture working-tree state before delegation and verify it is unchanged after every batch.
9. Run independent approved analyzers in parallel only when the host supports it and wait for the full batch before merging. Do not let analyzers delegate recursively. For every area, require either a valid analyzer report or a recorded parent fallback with a concrete cause and lost guarantees.
10. Before writing, present a short write report containing the approved plan, analyzed areas, profiles used, fallbacks, documents to create or change, and unresolved evidence. Ask for confirmation when the write set is broader or more destructive than the approved plan.
11. Validate names, links, source mappings, hashes, managed sections, report coverage, and the absence of analyzer writes before completion.
12. Report the requested intent, executed phases, delegation decision, profiles created or reused, fallbacks, changed documentation, checked relationships, unresolved evidence, and validation results. Do not delete stale managed profiles automatically; report them for explicit cleanup.

## Deterministic entry point

Use `scripts/codebase_analysis_ai.py` for documentation preflight, change collection, impact resolution, hash checks, link validation, project setup, and metadata refresh. Run `python scripts/codebase_analysis_ai.py --help` for available commands.
