# Documentation schema

Store machine-readable metadata in `docs/_meta/documentation-map.json`.

```json
{
  "schemaVersion": 1,
  "settings": {
    "documentationLanguage": "en",
    "languageDecisionSource": "existing-canonical-docs",
    "ignorePatterns": ["**/node_modules/**", "**/target/**"]
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
      "documentKind": "topic",
      "sections": {
        "coverage": "What this document covers",
        "context": "Context",
        "responsibilities": "Responsibilities",
        "howItWorks": "How it works",
        "activeFunctionality": "Active functionality",
        "relatedDocumentation": "Related documentation",
        "sources": "Sources"
      },
      "sourcePatterns": ["backend/src/**/security/**"],
      "sourceHashes": {
        "backend/src/main/java/security/SecurityConfig.java": "sha256-value"
      },
      "relatedDocuments": ["architecture.authentication-flow"]
    }
  }
}
```

`docs/_meta/state.json` is optional and purely informational: it may hold a checker schema version and Git baselines, but it is not required for bootstrap or migrate and is never used alone to declare documentation current. The documentation map and the checker report are authoritative.

Use a BCP 47 language tag such as `en`, `it`, or `pt-BR` for `documentationLanguage`. Set `languageDecisionSource` to `user`, `repository-policy`, or `existing-canonical-docs`. Do not guess either value when evidence is missing.

Document paths must be unique. Related IDs must exist. Document paths, source paths, and path patterns must remain inside the repository. Store them with repository-relative forward slashes; absolute paths and `..` segments are invalid.

`documentKind`, `sections`, and `metadata` are optional for backward compatibility with existing `schemaVersion: 1` maps. New documents created by `bootstrap` or `migrate` always declare `documentKind` and the required `sections`. The supported kinds and their required section keys are defined once in `scripts/codebase_analysis_ai/document_kinds.py`; the human reference in `document-style.md` mirrors that catalog without becoming a second machine contract.

`metadata` is an optional object for kind-specific fields such as decision-record status and supersession links. Unknown top-level metadata keys are preserved, not interpreted.

`sections` is an object whose keys are canonical, language-neutral section identifiers and whose values are the localized second-level headings actually used in the document. When a document declares `sections`, the validator requires every required key of its kind to be present and every declared label to appear as a unique `##` heading. Documents without `sections` keep the pre-existing legacy behavior and remain valid. An unknown `documentKind`, an unknown section key, a duplicate label, or a missing required key is an explicit map or document error.

Every bootstrapped or migrated documentation set must register `docs/index.md` with the stable ID `documentation.index`. Give it no source patterns or source hashes so ordinary source changes do not fan out to every document. Its `relatedDocuments` may contain top-level active documents or area indexes. Maintain the index explicitly whenever the active documentation set or its navigation changes. Never register files below `docs/_archive/`.

`taxonomy` stores the user-approved, parent-derived bootstrap classification. `sourceAreas` maps stable area IDs to candidate path patterns, evidence paths, and a reason. `documentationTopics` references only known source-area IDs. Later `update` and `audit` runs reuse this metadata instead of reinterpreting the complete repository. The taxonomy may be absent in maps created before this feature; report that delegation boundaries cannot be verified and use the parent fallback rather than inventing them.
