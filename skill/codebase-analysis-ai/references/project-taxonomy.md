# Project taxonomy

Derive repository shape and source ownership from the structural inventory and selectively read project files before creating folders. The deterministic inventory supplies evidence only; the parent agent owns every classification decision. Keep source macro-areas, documentation kinds, and documentation topics separate: source areas guide evidence collection and optional delegation; document kinds determine required sections, lifecycle, and index policy; documentation topics organize the parent-authored output.

- Monolith: organize by application areas such as architecture, backend, database, infrastructure, and operations.
- Full stack: separate frontend and backend while documenting shared flows under architecture.
- Microservices: use `docs/services/<service-name>/` plus shared architecture, infrastructure, and operations.
- Library or SDK: prioritize public API, integration, examples, compatibility, and release behavior.
- Mobile application: use application architecture, platforms, data, networking, security, and release.
- Infrastructure repository: prioritize environments, modules, deployment, security, state, and operations.
- Static site: prioritize HTML, styling, scripts, assets, SEO, accessibility, build, deployment, and content delivery.

Use this table as a starting point for document kinds, not as a mandatory folder template:

| Repository type | Document kinds to consider |
|---|---|
| Library or SDK | `api-reference`, `reference`, `architecture`, `runbook`, `decision-record` |
| Service or API | `area`, `architecture`, `data-model`, `api-reference`, `runbook`, `decision-record` |
| Monorepo | `area`, `architecture`, `reference`, `runbook`, `decision-record` |
| CLI | `reference`, `runbook`, `architecture`, `decision-record` |
| Static site | `architecture`, `reference`, `runbook`, `decision-record` |

These repository types are examples, not a closed catalog. Prefer terminology and boundaries declared by workspace files, manifests, build configuration, deployment configuration, and canonical documentation. When the evidence does not support a specific label, use a neutral `core` or module name and record what remains unresolved instead of forcing a known technology category.

Represent every proposed source area with `area`, `candidatePaths`, `evidence`, and `reason`. Represent every proposed documentation topic with `topic`, `candidatePaths`, `sourceAreas`, and `reason`. The parent assigns a `documentKind` and section set to each output document after the topic is selected; analyzers report kind needs but never select them. Create evidence-backed topics, not necessarily one subagent or one folder for every topic. A small repository may be analyzed entirely by the parent or one broad analyzer. Larger independent source areas may receive separate analyzers. The same source path may belong to multiple evidence areas when the questions differ.

Every generated area document must have evidence. Cross-area flows belong under `docs/architecture/flows/` rather than being duplicated. Decision records belong under `docs/decisions/`, dated analysis reports under `docs/_analysis/`, and neither is duplicated under an area. Do not create empty standard folders merely for symmetry.

Always create `docs/index.md` independently of the adaptive taxonomy. It is the canonical navigation layer, not a source macro-area or documentation topic. Link it to each top-level active document, area index, and kind index such as `docs/decisions/index.md`; exclude `docs/_archive/` and `docs/_analysis/`.

The taxonomy is adaptive, not a fixed folder template. Prefer repository concepts and service boundaries that readers already encounter in code, deployment, and operations. Do not create empty standard folders merely for symmetry.
