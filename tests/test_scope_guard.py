from __future__ import annotations

import os
import stat
import unittest

from fixtures import VaultFixture, guard


class ScopeGuardTests(VaultFixture):
    def test_scanner_is_bounded_and_does_not_disclose_sibling(self) -> None:
        self.write_scope("captures/inside.md", "inside query text\n")
        self.write_scope("developments/other.md", "unrelated\n")
        records = guard.scan_markdown(self.ctx, "query")
        self.assertEqual([record.scope_relative_path for record in records], ["captures/inside.md"])
        self.assertNotIn("secret", records[0].text)
        with self.assertRaises(guard.GuardFailure) as limit:
            guard.scan_markdown(self.ctx, "inside", max_files=1)
        self.assertEqual(limit.exception.code, "SCAN_LIMIT")

    def test_rejects_absolute_dot_dotdot_drive_unc_and_empty_paths(self) -> None:
        for target in ("", ".", "..", "captures/../secret.md", "/tmp/out.md", "C:/out.md", "\\\\server\\share\\out.md", "captures\\out.md"):
            with self.subTest(target=target), self.assertRaises(guard.GuardFailure) as caught:
                guard.resolve_target(self.ctx, target, allow_missing_leaf=True)
            self.assertEqual(caught.exception.code, "PATH_INVALID")

    def test_scope_cannot_be_vault_root_or_symlink_escape(self) -> None:
        root_data = dict(self.data, allowed_subdirectory=".")
        with self.assertRaises(guard.GuardFailure) as root:
            guard.validate_scope_config(root_data)
        self.assertEqual(root.exception.code, "CONFIG_INVALID")
        os.symlink(self.private, self.scope / "escape")
        with self.assertRaises(guard.GuardFailure) as link:
            guard.read_markdown(self.ctx, "escape/secret.md")
        self.assertEqual(link.exception.code, "SYMLINK_REJECTED")

    def test_special_file_and_invalid_utf8_fail_closed(self) -> None:
        fifo = self.scope / "captures" / "pipe.md"
        os.mkfifo(fifo)
        with self.assertRaises(guard.GuardFailure) as special:
            guard.read_markdown(self.ctx, "captures/pipe.md")
        self.assertEqual(special.exception.code, "SPECIAL_FILE_REJECTED")
        fifo.unlink()
        (self.scope / "captures" / "bad.md").write_bytes(b"\xff")
        with self.assertRaises(guard.GuardFailure) as encoding:
            guard.read_markdown(self.ctx, "captures/bad.md")
        self.assertEqual(encoding.exception.code, "INVALID_UTF8")

    def test_exclusive_create_expected_patch_and_hash_conflict(self) -> None:
        created = guard.exclusive_create(self.ctx, "captures/a.md", "first\n")
        self.assertEqual(created.text, "first\n")
        with self.assertRaises(guard.GuardFailure) as exists:
            guard.exclusive_create(self.ctx, "captures/a.md", "second\n")
        self.assertEqual(exists.exception.code, "ALREADY_EXISTS")
        updated = guard.patch_expected(self.ctx, "captures/a.md", created.sha256, "second\n")
        self.assertEqual(updated.text, "second\n")
        with self.assertRaises(guard.GuardFailure) as stale:
            guard.patch_expected(self.ctx, "captures/a.md", created.sha256, "third\n")
        self.assertEqual(stale.exception.code, "HASH_CONFLICT")

    def test_move_requires_hash_and_destination_does_not_exist(self) -> None:
        source = guard.exclusive_create(self.ctx, "captures/a.md", "move me\n")
        moved = guard.move_expected(self.ctx, "captures/a.md", "developments/a.md", source.sha256)
        self.assertEqual(moved.scope_relative_path, "developments/a.md")
        self.assertFalse((self.scope / "captures/a.md").exists())


if __name__ == "__main__":
    unittest.main()
