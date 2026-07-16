import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skill" / "codebase-analysis-ai" / "scripts"))

from codebase_analysis_ai.project_installer import START, update_managed_block  # noqa: E402


class InstallerTest(unittest.TestCase):
    def test_managed_block_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            block = f"{START}\nRule one.\n<!-- codebase-analysis-ai:end -->"
            update_managed_block(target, block)
            update_managed_block(target, block)
            content = target.read_text(encoding="utf-8")
            self.assertEqual(1, content.count(START))
            self.assertIn("Keep this.", content)


if __name__ == "__main__":
    unittest.main()

