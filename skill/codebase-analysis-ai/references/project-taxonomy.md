# Project taxonomy

Detect repository shape and source ownership before creating folders. Keep source macro-areas separate from documentation topics: source areas guide evidence collection and optional delegation; documentation topics organize the parent-authored output.

- Monolith: organize by application areas such as architecture, backend, database, infrastructure, and operations.
- Full stack: separate frontend and backend while documenting shared flows under architecture.
- Microservices: use `docs/services/<service-name>/` plus shared architecture, infrastructure, and operations.
- Library or SDK: prioritize public API, integration, examples, compatibility, and release behavior.
- Mobile application: use application architecture, platforms, data, networking, security, and release.
- Infrastructure repository: prioritize environments, modules, deployment, security, state, and operations.
- Static site: prioritize HTML, styling, scripts, assets, SEO, accessibility, build, deployment, and content delivery.

Create evidence-backed documentation topics, not necessarily one subagent or one folder for every topic. Represent each proposed topic with `topic`, `candidatePaths`, `sourceAreas`, and `reason`. A small repository may be analyzed entirely by the parent or one broad analyzer. Larger independent source areas may receive separate analyzers. The same source path may belong to multiple evidence areas when the questions differ.

Every generated area document must have evidence. Cross-area flows belong under `docs/architecture/flows/` rather than being duplicated. Do not create empty standard folders merely for symmetry.

The taxonomy is adaptive, not a fixed folder template. Prefer repository concepts and service boundaries that readers already encounter in code, deployment, and operations. Do not create empty standard folders merely for symmetry.
