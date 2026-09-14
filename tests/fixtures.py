from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
import scope_guard as guard  # noqa: E402


class VaultFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.mkdtemp(prefix="mind-garden-fixture-")
        self.vault = Path(self.tempdir) / "Fixture Vault"
        self.scope = self.vault / "Mind Garden"
        self.private = self.vault / "Private"
        self.scope.mkdir(parents=True)
        self.private.mkdir()
        for directory in ("captures", "developments", "distillations", "review"):
            (self.scope / directory).mkdir()
        self.private_note = self.private / "secret.md"
        self.private_note.write_text("outside-only confidential query", encoding="utf-8")
        self.data = {
            "schema_version": guard.CONFIG_VERSION,
            "vault_path": str(self.vault),
            "allowed_subdirectory": "Mind Garden",
            "limits": {"max_files": 100, "max_bytes": 1024 * 1024, "max_matches": 100},
        }
        self.ctx = guard.validate_scope_config(self.data)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def write_scope(self, relative: str, text: str) -> Path:
        path = self.scope / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
