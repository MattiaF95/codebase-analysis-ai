import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.project_detection import detect_areas  # noqa: E402


class ProjectDetectionTest(unittest.TestCase):
    def test_detects_static_site_without_requiring_subagents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")
            (root / "styles.css").write_text("body {}\n", encoding="utf-8")

            result = detect_areas(root)

            self.assertIn("static-site", result["areas"])
            self.assertIn("HTML", result["technologies"])
            self.assertIn("CSS", result["technologies"])
            topics = {topic["topic"]: topic for topic in result["documentationTopics"]}
            self.assertIn("seo", topics)
            self.assertEqual({"static-site"}, set(topics["seo"]["sourceAreas"]))
            self.assertTrue(topics["seo"]["candidatePaths"])
            self.assertTrue(topics["seo"]["reason"])

    def test_detects_html_only_site(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<html></html>\n", encoding="utf-8")

            result = detect_areas(root)

            self.assertIn("static-site", result["areas"])

    def test_does_not_classify_java_templates_as_static_site(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pom.xml").write_text("<project/>\n", encoding="utf-8")
            (root / "src" / "main" / "resources" / "templates").mkdir(parents=True)
            (root / "src" / "main" / "resources" / "templates" / "index.html").write_text("<html></html>\n", encoding="utf-8")
            (root / "src" / "main" / "resources" / "templates" / "styles.css").write_text("body {}\n", encoding="utf-8")

            result = detect_areas(root)

            self.assertIn("backend", result["areas"])
            self.assertNotIn("static-site", result["areas"])

    def test_topic_source_areas_do_not_include_unrelated_detected_areas(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pom.xml").write_text("<project/>\n", encoding="utf-8")
            (root / "Dockerfile").write_text("FROM eclipse-temurin\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_backend.py").write_text("def test_ok(): pass\n", encoding="utf-8")

            result = detect_areas(root)
            topics = {topic["topic"]: topic for topic in result["documentationTopics"]}

            self.assertEqual([], topics["testing"]["sourceAreas"])
            self.assertEqual({"backend", "infrastructure"}, set(topics["architecture"]["sourceAreas"]))


if __name__ == "__main__":
    unittest.main()
