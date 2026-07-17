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
  "taxonomy": {
    "sourceAreas": {
      "backend": {
        "candidatePaths": ["backend/**"],
        "evidence": ["pom.xml", "backend/pom.xml"],
        "reason": "independent application module"
      }
    },
    "documentationTopics": [
      {
        "topic": "authentication",
        "candidatePaths": ["backend/src/**/security/**"],
        "sourceAreas": ["backend"],
        "reason": "security configuration and request filters"
      }
    ]
  },
  "documents": {
    "documentation.index": {
      "path": "docs/index.md",
      "sourcePatterns": [],
      "sourceHashes": {},
      "relatedDocuments": ["backend.security.authentication"]
    },
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

Every bootstrapped or migrated documentation set must register `docs/index.md` with the stable ID `documentation.index`. Give it no source patterns or source hashes so ordinary source changes do not fan out to every document. Its `relatedDocuments` may contain top-level active documents or area indexes. Maintain the index explicitly whenever the active documentation set or its navigation changes. Never register files below `docs/_archive/`.

`taxonomy` stores the user-approved, parent-derived bootstrap classification. `sourceAreas` maps stable area IDs to candidate path patterns, evidence paths, and a reason. `documentationTopics` references only known source-area IDs. Later `update` and `audit` runs reuse this metadata instead of reinterpreting the complete repository. The taxonomy may be absent in maps created before this feature; report that delegation boundaries cannot be verified and use the parent fallback rather than inventing them.
