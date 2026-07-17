# Document style

## Resolve the documentation language

Use one language consistently across the maintained documentation set. Resolve it in this order:

1. Follow an explicit user instruction or repository documentation policy.
2. Otherwise, use the dominant language of reliable canonical existing documentation, prioritizing `docs/index.md`, the root `README.md`, contribution guides, and current active documents in `docs/`.
3. If documentation is absent, minimal, or does not provide reliable language evidence, ask the user which language to use and wait before writing, reviewing, or normalizing documentation.

Do not infer documentation language from programming-language keywords, identifiers, comments, commit messages, contributor names, locale, or geographic assumptions. If existing canonical documents use multiple languages without a clear dominant language, ask the user which language should become the standard before normalizing them.

Record the selected language and its decision source in `docs/_meta/documentation-map.json`. During incremental updates, preserve the established language and the language of the target document. Do not translate unrelated existing documents unless the user explicitly requests normalization.

Keep code identifiers, command names, API fields, protocol names, library names, and other canonical technical tokens unchanged. Translate their explanation, not the token itself. Translate template headings into the selected documentation language while preserving canonical filenames such as `README.md`.

## Write for humans without losing technical precision

- Start each document and major section with its purpose and context before implementation detail.
- Prefer familiar words and direct verbs. Use specialized terminology when it is the exact repository term, then explain what it means and why it matters.
- Expand uncommon, ambiguous, or domain-specific acronyms at first meaningful use in each standalone document, for example `Role-Based Access Control (RBAC)`. Use the acronym afterward.
- Do not expand an acronym when the expansion would be less recognizable than the established product, protocol, or repository term. Explain its role instead when needed.
- Use one main idea per sentence and short paragraphs. Split dense sentences instead of stacking qualifications.
- Name the acting component explicitly. Avoid vague subjects such as “it”, “the system”, or “this” when more than one component could be meant.
- Introduce lists, tables, diagrams, and code blocks with a sentence explaining what the reader should learn from them.
- Use lists for parallel items, tables for exact comparisons or mappings, and Mermaid diagrams only when relationships, ownership, or event order are materially clearer than prose.
- Put exact paths, symbols, commands, configuration keys, and endpoints in backticks. Explain their purpose and operational consequence in prose.
- Prefer concrete examples from the repository over generic examples. Never let an example introduce behavior that the source does not support.
- Avoid promotional language, filler, unexplained jargon, and paragraphs that merely restate a heading.

An engineer unfamiliar with the repository should be able to identify what the documented area does, why it exists, where it is implemented, how its main flow works, and what can change or fail.

## Organize from context to detail

Use this full sequence for topic documents, adapting labels to the selected language:

1. Purpose
2. Context
3. Responsibilities
4. How it works
5. Technologies and dependencies
6. Implementation details
7. Active functionality
8. Planned work and TODOs
9. Related documentation
10. Sources

Require Purpose, Context, How it works, Active functionality, Related documentation, and Sources in topic documents. Use the specialized root README, documentation index, and macro-area README templates for their respective roles while preserving the same context-to-detail progression.

Omit optional sections when they do not apply. Do not create empty headings or fill them with `None`, `Not applicable`, or unsupported placeholders.

Every related-document link must be relative and valid. Every source entry must use a repository-relative path.

## Documentation index

Use `docs/index.md` as the canonical entry point for active project documentation. Keep it concise and navigational: explain the documentation set, link to every top-level active document or area index, summarize each destination in one sentence, and link to documentation coverage. Do not list `docs/_archive/` as active documentation.

Read the index before selecting deeper documents. Verify it on every documentation change and update it when a document is added, removed, renamed, moved, or changes purpose. Do not traverse every indexed document when the selected intent requires only a bounded subset.
