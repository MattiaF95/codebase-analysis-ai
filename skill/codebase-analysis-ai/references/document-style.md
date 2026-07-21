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

- Start each document and major section with the information the reader needs before implementation detail.
- In the opening scope section, state immediately what the document contains and name the component, flow, decision, or repository area described by the file. Use one short paragraph of one or two lines, with no context, rationale, or implementation detail; keep it within two short sentences and 35 words.
- Prefer familiar words and direct verbs. Use specialized terminology when it is the exact repository term, then explain what it means and why it matters.
- Expand uncommon, ambiguous, or domain-specific acronyms at first meaningful use in each standalone document, for example `Role-Based Access Control (RBAC)`. Use the acronym afterward.
- Do not expand an acronym when the expansion would be less recognizable than the established product, protocol, or repository term. Explain its role instead when needed.
- Keep one main idea per sentence. Use as many sentences and paragraphs as needed to explain the idea without stacking unrelated qualifications.
- Name the acting component explicitly. Avoid vague subjects such as “it”, “the system”, or “this” when more than one component could be meant.
- Introduce lists, tables, diagrams, and code blocks with a sentence explaining what the reader should learn from them.
- Use lists for parallel items, tables for exact comparisons or mappings, and Mermaid diagrams only when relationships, ownership, or event order are materially clearer than prose.
- Make Mermaid source readable to a human without requiring a rendered preview. Use complete, immediately understandable participant and node names directly in relationships; never replace them with initials, acronyms, abbreviations, or short aliases such as `B` and `H` instead of `Browser` and `Homepage`.
- Put exact paths, symbols, commands, configuration keys, and endpoints in backticks. Explain their purpose and operational consequence in prose.
- Prefer concrete examples from the repository over generic examples. Never let an example introduce behavior that the source does not support.
- Avoid promotional language, filler, unexplained jargon, and paragraphs that merely restate a heading.

An engineer unfamiliar with the repository should be able to identify what the documented area does, why it exists, where it is implemented, how its main flow works, and what can change or fail. Do not remove context, rationale, contracts, edge cases, or failure behavior merely to reduce document length.

## Explain behavior as a narrative

Documentation must be explanatory, not a collection of labels or extracted code symbols. Use prose to connect the evidence and make the reader understand the behavior without opening the implementation immediately.

- For every important flow, explain the trigger, the acting component, the ordered steps, the decisions and conditions, the data or state that changes, and the resulting outcome.
- Explain why each relevant decision exists, what contract it protects, and what happens on validation failure, missing data, authorization failure, dependency failure, timeout, or other repository-specific edge cases.
- Use lists, tables, diagrams, and code blocks as supporting tools. Introduce and interpret each one in prose; never let a list or Mermaid diagram replace the explanation of the flow.
- Describe the normal path first, then the meaningful alternatives and failure paths. State which behavior is verified in source or tests and label inferences or unresolved evidence explicitly.
- Prefer a few complete paragraphs that tell the operational story over shallow sections containing only bullet points, filenames, class names, or endpoint inventories.
- For request, event, persistence, deployment, and authentication flows, name the entry point, the handoffs between components, the boundary crossed, and the observable result for the caller or operator.

## Classify detected problems

When the evidence reveals a problem, limitation, inconsistency, or meaningful uncertainty, add a detected-problems section whose heading is translated into the selected documentation language, for example `Problemi rilevati` in Italian or `Detected problems` in English. Render the template placeholder `detectedProblemsHeading` with that localized heading. Do not hide findings in general prose or in a list of limitations.

Classify each finding with exactly one type:

- `bug`: observed behavior contradicts an explicit contract, test, invariant, or stated requirement;
- `security`: weakness affecting confidentiality, integrity, authentication, authorization, secrets, or trust boundaries;
- `reliability`: failure, data-loss, consistency, recovery, timeout, rollback, or operational risk;
- `maintainability`: design inconsistency, duplication, hidden coupling, or change risk that does not currently prove incorrect behavior;
- `coverage-gap`: missing mapping, test, validation, observability, or evidence that prevents a confident conclusion;
- `documentation`: documentation is stale, incomplete, contradictory, or materially misleading.

Assign exactly one severity: `critical` (immediate severe impact or unsafe publication), `high` (likely material impact), `medium` (bounded impact or important operational risk), `low` (minor impact), or `info` (contextual observation without an actionable risk). Severity is about impact, not certainty.

Use this structure for every finding:

```markdown
### [medium][reliability] Short problem statement

- Evidenza: `repository-relative/path:line` or test/command result.
- Comportamento osservato: what the implementation does.
- Impatto: who or what can be affected and how.
- Confidenza: `alta`, `media`, or `bassa`, with the reason.
- Verifica: source-only, test, runtime, or external state checked.
- Azione consigliata: concrete next step, or `nessuna` when it is an accepted limitation.
```

Separate verified defects from risks, accepted design limitations, and unresolved questions. Never promote an inference to a bug without evidence. If no finding is supported, state that no problems were detected within the analyzed scope and explain what was not verified.

## Organize from context to detail

Use this full sequence for topic documents, adapting labels to the selected language:

1. What this document covers
2. Context
3. Responsibilities
4. How it works
5. Technologies and dependencies
6. Implementation details
7. Active functionality
8. Planned work and TODOs
9. Related documentation
10. Sources

Require What this document covers, Context, How it works, Active functionality, Related documentation, and Sources in topic documents. The opening section describes the file's contents; it does not explain why documentation is useful. Use the specialized root README, documentation index, and macro-area README templates for their respective roles while preserving the same context-to-detail progression. Do not impose a line, word, or paragraph limit on the remaining sections.

Omit optional sections when they do not apply. Do not create empty headings or fill them with `None`, `Not applicable`, or unsupported placeholders.

Every related-document link must be relative and valid. Every source entry must use a repository-relative path.

## Documentation index

Use `docs/index.md` as the canonical entry point for active project documentation. Keep it navigational: explain the documentation set, link to every top-level active document or area index, summarize each destination in one sentence, and link to documentation coverage. Do not list `docs/_archive/` as active documentation.

Read the index before selecting deeper documents. Verify it on every documentation change and update it when a document is added, removed, renamed, moved, or changes purpose. Do not traverse every indexed document when the selected intent requires only a bounded subset.
