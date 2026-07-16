# Documentation schema

Store machine-readable metadata in `docs/_meta/documentation-map.json`.

```json
{
  "schemaVersion": 1,
  "settings": {
    "documentationLanguage": "en",
    "languageDecisionSource": "existing-canonical-docs",
    "ignorePatterns": ["**/node_modules/**", "**/target/**"],
    "auditOnlyPatterns": ["**/test/**", "**/*.spec.ts"]
  },
  "documents": {
    "backend.security.authentication": {
      "path": "docs/backend/security/authentication.md",
      "sourcePatterns": ["backend/src/**/security/**"],
      "sourceHashes": {
        "backend/src/main/java/security/SecurityConfig.java": "sha256-value"
      },
      "relatedDocuments": ["architecture.authentication-flow"]
    }
  }
}
```

Use `docs/_meta/state.json` for checker schema version and optional informational Git baselines. Never use state alone to mark documentation current.

Use a BCP 47 language tag such as `en`, `it`, or `pt-BR` for `documentationLanguage`. Set `languageDecisionSource` to `user`, `repository-policy`, or `existing-canonical-docs`. Do not guess either value when evidence is missing.

Document paths must be unique. Related IDs must exist. Source paths use repository-relative forward slashes.
