from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import SKILL_ROOT, guard


class VendorContractTests(unittest.TestCase):
    def test_offline_manifest_pin_license_and_hash_audit(self) -> None:
        evidence = guard.verify_vendor(str(SKILL_ROOT))
        self.assertTrue(evidence["ok"])
        self.assertEqual(evidence["commit"], "8ccef29ae8624eccc734e77ced4a6e54baf5d83a")
        self.assertEqual(evidence["skills"], ["obsidian-cli", "obsidian-markdown", "obsidian-bases"])

    def test_only_root_skill_md_is_discoverable(self) -> None:
        discovered = sorted(
            path.relative_to(SKILL_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("SKILL.md")
            if ".workflow" not in path.relative_to(SKILL_ROOT).parts
            and ".git" not in path.relative_to(SKILL_ROOT).parts
        )
        self.assertEqual(discovered, ["SKILL.md"])

    def test_official_contracts_are_readable_and_match_pinned_manifest(self) -> None:
        manifest = json.loads(
            (SKILL_ROOT / "vendor/kepano-obsidian-skills/MANIFEST.json").read_text(encoding="utf-8")
        )
        vendor = SKILL_ROOT / "vendor/kepano-obsidian-skills"
        for name in ("obsidian-cli", "obsidian-markdown", "obsidian-bases"):
            with self.subTest(name=name):
                path = f"skills/{name}/UPSTREAM_SKILL.md"
                upstream_path = f"skills/{name}/SKILL.md"
                matches = [entry for entry in manifest["files"] if entry["path"] == path]
                self.assertEqual(len(matches), 1)
                entry = matches[0]
                self.assertEqual(entry["upstream_path"], upstream_path)
                contract = vendor / path
                self.assertTrue(contract.is_file())
                self.assertTrue(contract.read_text(encoding="utf-8"))
                self.assertEqual(hashlib.sha256(contract.read_bytes()).hexdigest(), entry["sha256"])
                self.assertFalse((vendor / upstream_path).exists())

    def test_verifier_rejects_missing_upstream_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(SKILL_ROOT / "vendor", root / "vendor")
            (root / "vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md").unlink()
            with self.assertRaises(guard.GuardFailure) as caught:
                guard.verify_vendor(str(root))
        self.assertEqual(caught.exception.code, "VENDOR_INVALID")

    def test_verifier_rejects_upstream_contract_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(SKILL_ROOT / "vendor", root / "vendor")
            contract = root / "vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md"
            contract.write_bytes(contract.read_bytes() + b"tampered\n")
            with self.assertRaises(guard.GuardFailure) as caught:
                guard.verify_vendor(str(root))
        self.assertEqual(caught.exception.code, "VENDOR_INVALID")

    def test_vendor_tree_is_read_only_baseline(self) -> None:
        manifest = SKILL_ROOT / "vendor/kepano-obsidian-skills/MANIFEST.json"
        self.assertTrue(manifest.is_file())
        self.assertEqual(guard.verify_vendor(str(SKILL_ROOT))["verified_files"], 7)


if __name__ == "__main__":
    unittest.main()
