import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.documentation_map import DocumentationMap  # noqa: E402
from codebase_analysis_ai.impact_graph import resolve_impact  # noqa: E402


class ImpactGraphTest(unittest.TestCase):
    def test_resolves_only_first_level_relationships(self):
        data = {
            "schemaVersion": 1,
            "settings": {},
            "documents": {
                "backend.security": {
                    "path": "docs/backend/security.md",
                    "sourcePatterns": ["src/security/**"],
                    "sourceHashes": {},
                    "relatedDocuments": ["architecture.auth"],
                },
                "architecture.auth": {
                    "path": "docs/architecture/auth.md",
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": ["operations.config"],
                },
                "operations.config": {
                    "path": "docs/operations/config.md",
                    "sourcePatterns": [],
                    "sourceHashes": {},
                    "relatedDocuments": [],
                },
            },
        }
        mapping = DocumentationMap(Path("map.json"), data)
        impact = resolve_impact(mapping, ["src/security/JwtService.java"])
        self.assertEqual(("backend.security",), impact.direct)
        self.assertEqual(("architecture.auth",), impact.related)
        self.assertNotIn("operations.config", impact.all_documents)

    def test_reports_unmapped_production_file(self):
        mapping = DocumentationMap(Path("map.json"), {"schemaVersion": 1, "settings": {}, "documents": {}})
        impact = resolve_impact(mapping, ["src/NewService.java", "docs/README.md"])
        self.assertEqual(("src/NewService.java",), impact.unmapped)

    def test_accepts_language_metadata(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {
                    "documentationLanguage": "pt-BR",
                    "languageDecisionSource": "user",
                },
                "documents": {},
            },
        )
        self.assertEqual([], mapping.validate())

    def test_rejects_incomplete_language_metadata(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {"documentationLanguage": "en"},
                "documents": {},
            },
        )
        self.assertIn(
            "settings must define documentationLanguage and languageDecisionSource together",
            mapping.validate(),
        )

    def test_accepts_agent_derived_taxonomy(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {},
                "taxonomy": {
                    "sourceAreas": {
                        "billing": {
                            "candidatePaths": ["services/billing/**"],
                            "evidence": ["services/billing/pyproject.toml"],
                            "reason": "independent service module",
                        }
                    },
                    "documentationTopics": [{
                        "topic": "billing-api",
                        "candidatePaths": ["services/billing/api/**"],
                        "sourceAreas": ["billing"],
                        "reason": "public API boundary",
                    }],
                },
                "documents": {},
            },
        )

        self.assertEqual([], mapping.validate())

    def test_rejects_unknown_topic_source_area(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {},
                "taxonomy": {
                    "sourceAreas": {},
                    "documentationTopics": [{
                        "topic": "security",
                        "candidatePaths": ["src/security/**"],
                        "sourceAreas": ["backend"],
                        "reason": "authentication boundary",
                    }],
                },
                "documents": {},
            },
        )

        self.assertIn(
            "taxonomy.documentationTopics[0]: unknown source area backend",
            mapping.validate(),
        )

    def test_rejects_empty_persisted_taxonomy(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {},
                "taxonomy": {"sourceAreas": {}, "documentationTopics": []},
                "documents": {},
            },
        )

        self.assertIn(
            "taxonomy.sourceAreas must define at least one approved source area",
            mapping.validate(),
        )

    def test_rejects_invalid_taxonomy_collection_types_without_crashing(self):
        mapping = DocumentationMap(
            Path("map.json"),
            {
                "schemaVersion": 1,
                "settings": {},
                "taxonomy": {
                    "sourceAreas": {
                        "backend": {
                            "candidatePaths": "backend/**",
                            "evidence": "pom.xml",
                            "reason": "application module",
                        }
                    },
                    "documentationTopics": [{
                        "topic": "security",
                        "candidatePaths": "src/security/**",
                        "sourceAreas": None,
                        "reason": "authentication boundary",
                    }],
                },
                "documents": {},
            },
        )

        errors = mapping.validate()

        self.assertIn(
            "taxonomy.sourceAreas.backend.candidatePaths must be a non-empty string array",
            errors,
        )
        self.assertIn("taxonomy.sourceAreas.backend.evidence must be a non-empty string array", errors)
        self.assertIn("taxonomy.documentationTopics[0].sourceAreas must be a string array", errors)


if __name__ == "__main__":
    unittest.main()
