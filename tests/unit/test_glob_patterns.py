import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.glob_patterns import compile_glob, glob_match  # noqa: E402


class GlobPatternsTest(unittest.TestCase):
    def test_single_star_does_not_cross_directories(self):
        self.assertTrue(glob_match("src/a.py", "src/*.py"))
        self.assertFalse(glob_match("src/a/b.py", "src/*.py"))

    def test_double_star_crosses_directories(self):
        self.assertTrue(glob_match("src/a/b.py", "src/**"))
        self.assertTrue(glob_match("src/a.py", "src/**"))

    def test_question_mark_matches_exactly_one_non_separator(self):
        self.assertTrue(glob_match("src/a.py", "src/?.py"))
        self.assertFalse(glob_match("src/ab.py", "src/?.py"))
        self.assertFalse(glob_match("src//.py", "src/?.py"))

    def test_double_star_slash_matches_zero_or_more_directories(self):
        self.assertTrue(glob_match("test/a.py", "**/test/**"))
        self.assertTrue(glob_match("src/test/a.py", "**/test/**"))
        self.assertTrue(glob_match("a.pem", "**/*.pem"))
        self.assertTrue(glob_match("dir/a.pem", "**/*.pem"))

    def test_extension_patterns(self):
        self.assertTrue(glob_match(".env.local", ".env.*"))
        self.assertTrue(glob_match(".env", ".env"))
        self.assertFalse(glob_match("nested/.env.local", ".env.*"))

    def test_default_map_patterns_keep_working(self):
        self.assertTrue(glob_match("docs/guide/intro.md", "docs/**"))
        self.assertTrue(glob_match("AGENTS.md", "**/AGENTS.md"))
        self.assertTrue(glob_match("pkg/AGENTS.md", "**/AGENTS.md"))
        self.assertTrue(glob_match("node_modules/pkg/index.js", "node_modules/**"))
        self.assertTrue(glob_match("app/node_modules/pkg/index.js", "**/node_modules/**"))

    def test_other_characters_are_literal(self):
        self.assertTrue(glob_match("src/a[1].py", "src/a[1].py"))
        self.assertFalse(glob_match("src/a1.py", "src/a[1].py"))

    def test_matching_is_case_sensitive_and_full_path(self):
        pattern = compile_glob("src/*.py")
        self.assertIsNotNone(pattern.match("src/a.py"))
        self.assertIsNone(pattern.match("SRC/a.py"))
        self.assertIsNone(pattern.match("x/src/a.py"))


if __name__ == "__main__":
    unittest.main()
