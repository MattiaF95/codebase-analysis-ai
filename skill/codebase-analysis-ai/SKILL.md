---
name: codebase-analysis-ai
description: Perform agentic, evidence-based codebase analysis to create, update, migrate, or audit repository documentation covering architecture, code flows, APIs, schemas, security boundaries, configuration, and delivery pipelines. Use after code, configuration, commit, PR, merge, rebase, or pull changes when documentation may need synchronization, or when an explicit documentation review is requested. Default to Git-diff-based incremental analysis and inspect only directly impacted documents and their first-level links. Never scan the entire repository or create documentation from scratch unless the user explicitly requests a full documentation bootstrap. If documentation is missing and bootstrap was not explicit, ask whether to initialize it or stop. Do not use for generic writing, standalone code explanation, or a general code-quality review unrelated to documentation.
---

# Codebase Analysis AI

Keep repository documentation aligned with implementation changes while minimizing repository reads and repeated analysis.

## Select one mode

Choose exactly one mode before reading additional references.

- `setup`: Install the skill, persistent agent rules, deterministic runtime, Git hooks, or GitHub Action. Require an explicit setup request. Read `references/setup-mode.md` and `references/automation.md`.
- `bootstrap`: Create a complete documentation system from scratch. Require an explicit request to scan the full repository. Read `references/bootstrap-mode.md`, `references/project-taxonomy.md`, `references/document-style.md`, and `references/subagent-contract.md`.
- `update`: Update existing documentation from current Git changes, a commit, or a commit range. This is the default synchronization mode. Read `references/update-mode.md`, `references/change-detection.md`, `references/impact-resolution.md`, and `references/document-style.md`.
- `audit`: Inspect documentation accuracy, readability, language consistency, and link consistency without changing files. Read `references/audit-mode.md`, `references/quality-rules.md`, and `references/document-style.md`.
- `migrate`: Index and normalize existing documentation that has no Codebase Analysis AI metadata. Read `references/migrate-mode.md`, `references/documentation-schema.md`, `references/naming-conventions.md`, and `references/document-style.md`.

Do not read references for unrelated modes.

## Existing-documentation policy

`existingDocumentationPolicy: ask` is the default safety policy for `bootstrap` and any request to create documentation from zero. Before generating documents, run `scripts/codebase_analysis_ai.py docs-state` (or perform the equivalent path-only check). If any existing repository documentation is present, stop and ask the user whether to:

- adopt and index it with `migrate`;
- update or integrate it incrementally; or
- explicitly replace it with a new bootstrap.

The preflight needs only the first matching document path; it checks common text, markup, PDF, Word, PowerPoint, Excel, OpenDocument, and RTF formats plus canonical names such as `README`, `LICENSE`, and `CHANGELOG`. It does not open the file. After the user's choice, read the other relevant documents. Wait for the user's choice before reading the repository broadly or writing files. This gate does not apply when the user explicitly selects `update`, `audit`, or `migrate`.

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

## Common execution contract

1. Resolve the repository root and current Git state.
2. Select one mode.
3. Load only the references required for that mode.
4. Run deterministic scripts before agent analysis whenever possible.
5. Use parallel subagents only for independent macro-areas and only when the host supports them. Otherwise execute the same report contract sequentially.
6. Validate names, links, source mappings, hashes, and managed sections before completion.
7. Report changed documentation, checked direct relationships, unresolved evidence, and validation results.

## Deterministic entry point

Use `scripts/codebase_analysis_ai.py` for documentation preflight, change collection, impact resolution, hash checks, link validation, project setup, and metadata refresh. Run `python scripts/codebase_analysis_ai.py --help` for available commands.
