# Naming conventions

- Directories and ordinary Markdown files: lowercase `kebab-case`.
- Python modules: lowercase `snake_case.py`.
- Workflow files: lowercase `kebab-case.yml`.
- JSON keys: `camelCase`.
- Document IDs: lowercase dot-separated namespaces. Keep an existing ID stable when a document moves; change only the recorded `path`.
- Documentation areas and kind directories: lowercase `kebab-case` (`docs/backend-api/`, `docs/decisions/`, `docs/runbooks/`).
- Decision records: `ADR-NNNN-<slug>.md` with exactly four digits, unique and consistent with the recorded decision. Never renumber or rename an existing ADR automatically; `docs/adr/` remains a recognized legacy alias of `docs/decisions/`.
- Analysis reports: dated snapshots under `docs/_analysis/`; they are evidence, not active navigation entries.
- Git hooks: official Git names such as `pre-push` and `post-merge`.
- Technology names in prose: preserve official casing.
- Headings: sentence case.

Preserve canonical filenames exactly: `README.md`, `SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `LICENSE`, `CHANGELOG.md`, and `CONTRIBUTING.md`.

Validate case-sensitive uniqueness even on case-insensitive filesystems.
