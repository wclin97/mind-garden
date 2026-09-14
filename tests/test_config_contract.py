from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.fixtures import SKILL_ROOT, guard


class ConfigContractTests(unittest.TestCase):
    @staticmethod
    def _v11_policy(**overrides: object) -> dict[str, object]:
        return {**guard.DEFAULT_EXTERNAL_ENRICHMENT, **overrides}

    @classmethod
    def _v11_data(cls, vault: Path, **overrides: object) -> dict[str, object]:
        data: dict[str, object] = {
            "schema_version": guard.CONFIG_VERSION,
            "vault_path": str(vault),
            "allowed_subdirectory": "Mind Garden",
            "external_enrichment": cls._v11_policy(),
        }
        data.update(overrides)
        return data

    def test_schema_is_closed_and_v11_example_defaults_to_automatic(self) -> None:
        schema = json.loads((SKILL_ROOT / "config.schema.json").read_text(encoding="utf-8"))
        example = json.loads((SKILL_ROOT / "config.example.json").read_text(encoding="utf-8"))
        current = schema["$defs"]["current_v1_1"]
        policy = schema["$defs"]["external_enrichment"]
        self.assertFalse(current["additionalProperties"])
        self.assertEqual(
            current["required"],
            ["schema_version", "vault_path", "allowed_subdirectory", "external_enrichment"],
        )
        self.assertEqual(example["schema_version"], guard.CONFIG_VERSION)
        self.assertEqual(example["external_enrichment"], guard.DEFAULT_EXTERNAL_ENRICHMENT)
        self.assertIn("/absolute/path/to/", example["vault_path"])
        self.assertEqual(
            {key: definition["maximum"] for key, definition in policy["properties"].items() if key != "mode"},
            guard.EXTERNAL_ENRICHMENT_MAXIMA,
        )
        self.assertNotIn("token", json.dumps(schema).lower())

    def test_v10_remains_valid_but_normalizes_to_offline_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "Fixture Vault"
            (vault / "Mind Garden").mkdir(parents=True)
            legacy = {
                "schema_version": guard.LEGACY_CONFIG_VERSION,
                "vault_path": str(vault),
                "allowed_subdirectory": "Mind Garden",
            }
            context = guard.validate_scope_config(legacy)
            self.assertEqual(context.external_enrichment.mode, "offline")
            self.assertEqual(legacy["schema_version"], guard.LEGACY_CONFIG_VERSION)
            self.assertNotIn("external_enrichment", legacy)

    def test_v11_requires_complete_closed_policy_and_rejects_secrets_or_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "Fixture Vault"
            (vault / "Mind Garden").mkdir(parents=True)
            base = self._v11_data(vault)
            context = guard.validate_scope_config(base)
            self.assertEqual(context.external_enrichment.mode, "automatic")
            self.assertEqual(context.external_enrichment.max_search_results, 5)
            invalid_values = [
                {**base, "external_enrichment": {"mode": "automatic"}},
                {**base, "external_enrichment": self._v11_policy(mode="ask")},
                {**base, "external_enrichment": self._v11_policy(max_search_results=11)},
                {**base, "external_enrichment": self._v11_policy(max_image_downloads=4)},
                {**base, "external_enrichment": self._v11_policy(max_image_bytes=8 * 1024 * 1024 + 1)},
                {**base, "external_enrichment": self._v11_policy(max_excerpt_chars=1001)},
                {**base, "external_enrichment": {**self._v11_policy(), "provider": "not-allowed"}},
                {**base, "endpoint": "https://not-allowed.example"},
                {**base, "credential": "not-allowed"},
            ]
            for candidate in invalid_values:
                with self.subTest(candidate=candidate), self.assertRaises(guard.GuardFailure) as caught:
                    guard.validate_scope_config(candidate)
                self.assertEqual(caught.exception.code, "CONFIG_INVALID")

    def test_runtime_limits_enforce_schema_maxima(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "Fixture Vault"
            (vault / "Mind Garden").mkdir(parents=True)
            base = self._v11_data(vault)
            exact = dict(base, limits=dict(guard.LIMIT_MAXIMA))
            self.assertEqual(dict(guard.validate_scope_config(exact).limits), guard.LIMIT_MAXIMA)
            for key, maximum in guard.LIMIT_MAXIMA.items():
                with self.subTest(key=key), self.assertRaises(guard.GuardFailure) as caught:
                    guard.validate_scope_config(dict(base, limits={key: maximum + 1}))
                self.assertEqual(caught.exception.code, "CONFIG_INVALID")

    def test_root_contract_files_are_not_ignored(self) -> None:
        ignore_rules = (SKILL_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn("config", ignore_rules)
        self.assertIn("__pycache__/", ignore_rules)

    @classmethod
    def _write_valid_config(cls, config_path: Path, temporary_root: Path) -> dict[str, object]:
        vault = temporary_root / "Fixture Vault"
        (vault / "Mind Garden").mkdir(parents=True)
        data = cls._v11_data(vault)
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
