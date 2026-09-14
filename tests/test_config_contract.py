from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fixtures import SKILL_ROOT, guard


class ConfigContractTests(unittest.TestCase):
    def test_schema_is_closed_and_example_is_placeholder_only(self) -> None:
        schema = json.loads((SKILL_ROOT / "config.schema.json").read_text(encoding="utf-8"))
        example = json.loads((SKILL_ROOT / "config.example.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], ["schema_version", "vault_path", "allowed_subdirectory"])
        self.assertEqual(example["schema_version"], "mind-garden-local-config/1.0")
        self.assertIn("/absolute/path/to/", example["vault_path"])
        self.assertNotIn("token", json.dumps(schema).lower())

    def test_root_contract_files_are_not_ignored(self) -> None:
        ignore_rules = (SKILL_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn("config", ignore_rules)
        self.assertIn("__pycache__/", ignore_rules)

    @staticmethod
    def _write_valid_config(config_path: Path, temporary_root: Path) -> dict[str, object]:
        vault = temporary_root / "Fixture Vault"
        (vault / "Mind Garden").mkdir(parents=True)
        data: dict[str, object] = {
            "schema_version": guard.CONFIG_VERSION,
            "vault_path": str(vault),
            "allowed_subdirectory": "Mind Garden",
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def test_load_config_uses_only_an_absolute_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "explicit-config.json"
            self._write_valid_config(config_path, root)
            with patch.dict(os.environ, {"MIND_GARDEN_CONFIG": str(config_path)}, clear=True):
                context = guard.load_config()
            self.assertEqual(context.config_path, str(config_path))
            self.assertEqual(context.scope_vault_relative_posix, "Mind Garden")

    def test_load_config_uses_absolute_xdg_location_without_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            xdg_root = root / "xdg"
            config_path = xdg_root / "mind-garden" / "config.json"
            self._write_valid_config(config_path, root)
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_root)}, clear=True):
                context = guard.load_config()
            self.assertEqual(context.config_path, str(config_path))

    def test_load_config_rejects_relative_explicit_or_xdg_locations(self) -> None:
        for environment in ({"MIND_GARDEN_CONFIG": "relative-config.json"}, {"XDG_CONFIG_HOME": "relative-xdg"}):
            with self.subTest(environment=environment), patch.dict(os.environ, environment, clear=True):
                with self.assertRaises(guard.GuardFailure) as caught:
                    guard.load_config()
            self.assertEqual(caught.exception.code, "CONFIG_INVALID")

    def test_load_config_missing_temp_default_does_not_read_or_create_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            with patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                with self.assertRaises(guard.GuardFailure) as caught:
                    guard.load_config()
            self.assertEqual(caught.exception.code, "CONFIG_MISSING")
            self.assertFalse((home / ".config" / "mind-garden" / "config.json").exists())


if __name__ == "__main__":
    unittest.main()
