import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.document_kinds import (  # noqa: E402
    DOCUMENT_KINDS,
    SECTION_LABELS,
    document_kind,
    known_kind_ids,
    section_contract_errors,
)


class DocumentKindsTest(unittest.TestCase):
    def test_catalog_covers_every_required_kind(self):
        self.assertEqual(
            {
                "project-readme",
                "documentation-index",
                "area",
                "topic",
                "architecture",
                "api-reference",
                "data-model",
                "runbook",
                "test-strategy",
                "backlog",
                "decision-record",
                "reference",
                "analysis-report",
            },
            set(known_kind_ids()),
        )

    def test_every_kind_uses_known_section_keys(self):
        for kind in DOCUMENT_KINDS.values():
            with self.subTest(kind=kind.id):
                self.assertTrue(kind.required_sections)
                self.assertEqual(set(), set(kind.required_sections) - set(SECTION_LABELS))
                self.assertEqual(set(), set(kind.recommended_sections) - set(SECTION_LABELS))
                self.assertEqual(set(), set(kind.required_sections) & set(kind.recommended_sections))
                self.assertIn(kind.lifecycle, {"living", "immutable-after-acceptance", "snapshot"})
                self.assertIn(kind.index_policy, {"indexed", "kind-index", "excluded"})

    def test_decision_records_are_immutable_and_have_no_sources(self):
        kind = document_kind("decision-record")

        self.assertIsNotNone(kind)
        assert kind is not None
        self.assertEqual("immutable-after-acceptance", kind.lifecycle)
        self.assertEqual("kind-index", kind.index_policy)
        self.assertFalse(kind.source_patterns_required)
        self.assertIn("decision", kind.required_sections)
        self.assertIn("consequences", kind.required_sections)

    def test_unknown_kind_is_not_returned(self):
        self.assertIsNone(document_kind("not-a-kind"))
        self.assertIsNone(document_kind(None))

    def test_sections_must_cover_required_keys_and_unique_labels(self):
        errors = section_contract_errors("topic", {"coverage": "Cosa copre", "context": "Contesto"})

        self.assertTrue(any("missing required sections" in error for error in errors))

        duplicate = section_contract_errors(
            "topic",
            {
                "coverage": "Stesso titolo",
                "context": "Stesso titolo",
                "responsibilities": "Responsabilità",
                "howItWorks": "Come funziona",
                "activeFunctionality": "Funzionalità attive",
                "relatedDocumentation": "Documentazione correlata",
                "sources": "Fonti",
            },
        )
        self.assertTrue(any("duplicates the heading label" in error for error in duplicate))

        unknown = section_contract_errors(
            "topic",
            {
                "coverage": "Cosa copre",
                "context": "Contesto",
                "unknown": "Titolo",
            },
        )
        self.assertTrue(any("unknown section key" in error for error in unknown))

    def test_section_contract_is_optional_for_legacy_documents(self):
        self.assertEqual([], section_contract_errors("topic", None))
        self.assertEqual([], section_contract_errors(None, {"coverage": "Qualsiasi"}))


if __name__ == "__main__":
    unittest.main()
