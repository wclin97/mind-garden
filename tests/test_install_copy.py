from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import SKILL_ROOT, guard


class InstallCopyTests(unittest.TestCase):
    def test_complete_skill_copies_to_a_disposable_install_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mind-garden-install-fixture-") as temporary:
            destination = Path(temporary) / "mind-garden"
            shutil.copytree(
                SKILL_ROOT,
                destination,
                ignore=shutil.ignore_patterns(".git", ".workflow", "__pycache__", "*.pyc"),
            )
            discovered = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("SKILL.md"))
            self.assertEqual(discovered, ["SKILL.md"])
            for relative in (
                "README.md",
                "config.schema.json",
                "config.example.json",
                "scripts/scope_guard.py",
                "references/external-enrichment.md",
                "references/authorization-and-scope.md",
                "references/local-configuration.md",
                "references/mode-protocols.md",
                "references/artifact-schema.md",
                "tests/test_install_copy.py",
            ):
                self.assertEqual((destination / relative).read_bytes(), (SKILL_ROOT / relative).read_bytes())
            self.assertTrue(guard.verify_vendor(str(destination))["ok"])


if __name__ == "__main__":
    unittest.main()
