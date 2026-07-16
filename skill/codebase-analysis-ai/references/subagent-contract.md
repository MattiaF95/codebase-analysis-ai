# Subagent contract

Use independent area analyzers during bootstrap or an explicitly broad audit. The parent must attempt runtime delegation for every detected macro-area. A subagent is a temporary runtime worker created through the host's delegation mechanism; it does not need a persistent profile file in the repository.

Each analyzer receives a self-contained brief with its area, allowed repository-relative paths, excluded paths, evidence questions, read-only boundary, and documentation-language decision. Return structured JSON with this shape:

```json
{
  "area": "backend",
  "paths": ["backend/src"],
  "technologies": ["Java", "Spring Boot"],
  "responsibilities": ["Expose REST APIs"],
  "entryPoints": [{"path": "...", "purpose": "..."}],
  "dependencies": {"internal": [], "external": []},
  "flows": [{"name": "Authentication", "sources": []}],
  "security": [],
  "terminology": [{"term": "RBAC", "definition": "Role-Based Access Control", "sources": []}],
  "activeFunctionality": [],
  "todos": [{"path": "...", "line": 1, "text": "..."}],
  "documentationNeeded": [],
  "uncertainties": [],
  "confidence": 0.9
}
```

Report terminology only when its meaning is supported by repository evidence. The orchestrator merges reports, resolves duplicate flows and definitions, selects the documentation language, and assigns cross-area documentation. Do not let subagents independently choose a language or writing style.

Do not pass conclusions from one analyzer to another. The parent orchestrator validates every report before using it. If the host exposes no runtime delegation mechanism, produce the same reports sequentially in the parent context and state the concrete capability limitation; “no pre-written agent file” is not a valid reason.
