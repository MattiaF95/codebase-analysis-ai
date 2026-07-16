# Project taxonomy

Detect repository shape before creating folders.

- Monolith: organize by application areas such as architecture, backend, database, infrastructure, and operations.
- Full stack: separate frontend and backend while documenting shared flows under architecture.
- Microservices: use `docs/services/<service-name>/` plus shared architecture, infrastructure, and operations.
- Library or SDK: prioritize public API, integration, examples, compatibility, and release behavior.
- Mobile application: use application architecture, platforms, data, networking, security, and release.
- Infrastructure repository: prioritize environments, modules, deployment, security, state, and operations.

Create only detected areas. Every macro-area receives an essential `README.md`. Cross-area flows belong under `docs/architecture/flows/` rather than being duplicated.

The taxonomy is adaptive, not a fixed folder template. Prefer repository concepts and service boundaries that readers already encounter in code, deployment, and operations. Do not create empty standard folders merely for symmetry.
