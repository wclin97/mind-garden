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
        for kwargs in ({"max_files": 0}, {"max_bytes": guard.LIMIT_MAXIMA["max_bytes"] + 1}, {"max_matches": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(guard.GuardFailure) as invalid:
                guard.scan_markdown(self.ctx, "inside", **kwargs)
            self.assertEqual(invalid.exception.code, "SCAN_LIMIT")

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

    def test_create_lazily_initializes_only_fixed_artifact_parent(self) -> None:
        os.rmdir(self.scope / "captures")
        preview_target = guard.resolve_target(
            self.ctx, "captures/new.md", purpose="create", allow_missing_leaf=True
        )
        self.assertTrue(preview_target.endswith("/captures/new.md"))
        self.assertFalse((self.scope / "captures").exists())

        created = guard.exclusive_create(self.ctx, "captures/new.md", "created\n")
        self.assertEqual(created.text, "created\n")
        self.assertTrue((self.scope / "captures").is_dir())

        os.rmdir(self.scope / "developments")
        with self.assertRaises(guard.GuardFailure) as missing_read:
            guard.read_markdown(self.ctx, "developments/missing.md")
        self.assertEqual(missing_read.exception.code, "NOT_FOUND")
        self.assertFalse((self.scope / "developments").exists())

        os.rmdir(self.scope / "review")
        base = guard.exclusive_create_text(self.ctx, "review/Mind Garden Review.base", "views: []\n")
        self.assertEqual(base.text, "views: []\n")

        (self.scope / "arbitrary").mkdir()
        for target in ("arbitrary/new.md", "captures/nested/new.md", "root.md"):
            with self.subTest(target=target), self.assertRaises(guard.GuardFailure) as caught:
                guard.exclusive_create(self.ctx, target, "blocked\n")
            self.assertEqual(caught.exception.code, "PATH_INVALID")

    def test_create_rejects_symlink_and_special_artifact_parent(self) -> None:
        os.rmdir(self.scope / "distillations")
        os.symlink(self.private, self.scope / "distillations")
        with self.assertRaises(guard.GuardFailure) as link:
            guard.exclusive_create(self.ctx, "distillations/new.md", "blocked\n")
        self.assertEqual(link.exception.code, "SYMLINK_REJECTED")

        os.rmdir(self.scope / "review")
        (self.scope / "review").write_text("not a directory", encoding="utf-8")
        with self.assertRaises(guard.GuardFailure) as special:
            guard.exclusive_create_text(self.ctx, "review/Mind Garden Review.base", "views: []\n")
        self.assertEqual(special.exception.code, "SPECIAL_FILE_REJECTED")

    def test_invalid_utf8_writes_do_not_create_or_modify_artifacts(self) -> None:
        os.rmdir(self.scope / "distillations")
        with self.assertRaises(guard.GuardFailure) as create_error:
            guard.exclusive_create(self.ctx, "distillations/new.md", "\ud800")
        self.assertEqual(create_error.exception.code, "INVALID_UTF8")
        self.assertFalse((self.scope / "distillations").exists())

        os.rmdir(self.scope / "review")
        with self.assertRaises(guard.GuardFailure) as base_error:
            guard.exclusive_create_text(self.ctx, "review/new.base", "\ud800")
        self.assertEqual(base_error.exception.code, "INVALID_UTF8")
        self.assertFalse((self.scope / "review").exists())

        original = guard.exclusive_create(self.ctx, "captures/original.md", "original\n")
        with self.assertRaises(guard.GuardFailure) as patch_error:
            guard.patch_expected(self.ctx, "captures/original.md", original.sha256, "\ud800")
        self.assertEqual(patch_error.exception.code, "INVALID_UTF8")
        self.assertEqual(guard.read_markdown(self.ctx, "captures/original.md").text, "original\n")

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

    def test_move_fails_closed_without_mutating_source_or_destination(self) -> None:
        source = guard.exclusive_create(self.ctx, "captures/a.md", "move me\n")
        os.rmdir(self.scope / "developments")
        with self.assertRaises(guard.GuardFailure) as unsupported:
            guard.move_expected(self.ctx, "captures/a.md", "developments/a.md", source.sha256)
        self.assertEqual(unsupported.exception.code, "UNSUPPORTED_SAFE_IO")
        self.assertEqual(guard.read_markdown(self.ctx, "captures/a.md").text, "move me\n")
        self.assertFalse((self.scope / "developments").exists())


if __name__ == "__main__":
    unittest.main()
