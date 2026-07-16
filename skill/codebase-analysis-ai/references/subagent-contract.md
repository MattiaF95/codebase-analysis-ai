# Subagent contract

Use independent area analyzers only during bootstrap or an explicitly broad audit. Return structured JSON with this shape:

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

Do not pass conclusions from one analyzer to another. If subagents are unavailable, produce the same reports sequentially.
