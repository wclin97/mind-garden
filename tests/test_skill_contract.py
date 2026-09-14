from __future__ import annotations

import re
import unittest

from fixtures import SKILL_ROOT, guard


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.references = "\n".join(path.read_text(encoding="utf-8") for path in (SKILL_ROOT / "references").glob("*.md"))

    def test_is_discoverable_and_declares_five_modes(self) -> None:
        self.assertTrue(self.skill.startswith("---\nname: mind-garden\n"))
        for mode in ("capture", "develop", "connect", "distill", "review"):
            self.assertRegex(self.skill, rf"### {mode}\b")

    def test_requires_exact_vendor_paths_and_guard_boundary(self) -> None:
        for name in ("obsidian-cli", "obsidian-markdown", "obsidian-bases"):
            self.assertIn(f"vendor/kepano-obsidian-skills/skills/{name}/UPSTREAM_SKILL.md", self.skill)
        self.assertIn("scope_guard.py", self.skill)
        self.assertIn("verify-vendor", self.skill)
        self.assertIn("unsaved draft", self.skill)

    def test_mode_protocol_requires_preview_confirmation_and_readback(self) -> None:
        for word in ("preview", "confirmation", "read back", "source hashes"):
            self.assertIn(word, self.skill.lower())
        self.assertIn("Original expression", self.skill)
        self.assertIn("path-qualified", self.skill)

    def test_fixed_artifact_parent_initialization_contract(self) -> None:
        product = self.skill + "\n" + self.references
        for directory in ("captures", "developments", "distillations", "review"):
            self.assertIn(directory, guard.ARTIFACT_DIRECTORIES)
        self.assertIn("preview target resolution never creates", product.lower())
        self.assertIn("reads/patches never initialize", product.lower())
        self.assertIn("missing direct", product.lower())
        self.assertIn("move_expected", product)
        self.assertIn("always fails closed", product.lower())
        self.assertIn("O_NOFOLLOW_ANY", product)
        self.assertIn("any directory inside the authorized scope tree", product.lower())
        self.assertIn("target leaf", product.lower())

    def test_static_capability_and_cli_audit(self) -> None:
        product = self.skill + "\n" + self.references
        for forbidden in ("obsidian search", "obsidian backlinks", "obsidian tags", "obsidian tasks", "daily:*", "file=", "MCP", "embedding", "database/index", "runtime dependency installation", "automatic Git"):
            self.assertIn(forbidden, product)
        # No executable tooling is introduced in the product except the guard.
        scripts = list((SKILL_ROOT / "scripts").glob("*.py"))
        self.assertEqual([script.name for script in scripts], ["scope_guard.py"])


if __name__ == "__main__":
    unittest.main()
