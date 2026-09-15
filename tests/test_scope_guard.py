from __future__ import annotations

import os
import stat
import unittest
from pathlib import Path
from unittest import mock

from tests.fixtures import VaultFixture, guard


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

    def test_whole_vault_reads_siblings_but_writes_remain_in_configured_scope(self) -> None:
        outside = guard.read_vault_markdown(self.ctx, "Private/secret.md")
        self.assertEqual(outside.vault_relative_path, "Private/secret.md")
        self.assertIsNone(outside.scope_relative_path)
        self.assertIn("outside-only confidential query", outside.text)

        matches = guard.scan_vault_markdown(self.ctx, "confidential query")
        self.assertEqual([record.vault_relative_path for record in matches], ["Private/secret.md"])
        self.assertIsNone(matches[0].scope_relative_path)

        inside = guard.exclusive_create(self.ctx, "captures/write-target.md", "inside\n")
        self.assertEqual(guard.scope_path_for_write(self.ctx, inside), "captures/write-target.md")
        original = self.private_note.read_text(encoding="utf-8")
        with mock.patch.object(guard, "patch_expected", wraps=guard.patch_expected) as patch:
            with self.assertRaises(guard.GuardFailure) as write_target:
                guard.scope_path_for_write(self.ctx, outside)
        self.assertEqual(write_target.exception.code, "PATH_INVALID")
        patch.assert_not_called()

        with self.assertRaises(guard.GuardFailure) as create_outside:
            guard.exclusive_create(self.ctx, "Private/new.md", "blocked\n")
        self.assertEqual(create_outside.exception.code, "PATH_INVALID")
        with self.assertRaises(guard.GuardFailure) as patch_outside:
            guard.patch_expected(self.ctx, "../Private/secret.md", outside.sha256, "blocked\n")
        self.assertEqual(patch_outside.exception.code, "PATH_INVALID")
        self.assertEqual(self.private_note.read_text(encoding="utf-8"), original)
        self.assertFalse((self.private / "new.md").exists())

    def test_custom_allowed_subdirectory_writes_fixed_artifacts_only_there(self) -> None:
        custom_name = "Idea Shelf"
        custom_scope = self.vault / custom_name
        custom_scope.mkdir()
        custom_data = {**self.data, "allowed_subdirectory": custom_name}
        custom_ctx = guard.validate_scope_config(custom_data)

        for relative in (
            "captures/custom.md",
            "developments/custom.md",
            "distillations/custom.md",
            "review/custom.md",
        ):
            with self.subTest(relative=relative):
                created = guard.exclusive_create(custom_ctx, relative, "custom scope\n")
                self.assertEqual(created.scope_relative_path, relative)
                self.assertEqual(created.vault_relative_path, f"{custom_name}/{relative}")
                self.assertTrue((custom_scope / relative).is_file())
                self.assertFalse((self.scope / relative).exists())

        with self.assertRaises(guard.GuardFailure) as old_scope:
            guard.exclusive_create(custom_ctx, "Mind Garden/captures/not-allowed.md", "blocked\n")
        self.assertEqual(old_scope.exception.code, "PATH_INVALID")
        with self.assertRaises(guard.GuardFailure) as sibling:
            guard.exclusive_create(custom_ctx, "../Private/not-allowed.md", "blocked\n")
        self.assertEqual(sibling.exception.code, "PATH_INVALID")
        self.assertFalse((self.private / "not-allowed.md").exists())

    def test_resolve_vault_target_accepts_only_regular_markdown_files(self) -> None:
        self.assertEqual(
            guard.resolve_vault_target(self.ctx, "Private/secret.md"),
            os.path.realpath(self.private_note),
        )
        (self.private / "directory.md").mkdir()
        os.symlink(self.private_note, self.private / "symlink.md")
        os.mkfifo(self.private / "pipe.md")
        (self.private / "plain.txt").write_text("not markdown", encoding="utf-8")

        for relative, code in (
            ("Private/directory.md", "SPECIAL_FILE_REJECTED"),
            ("Private/symlink.md", "SYMLINK_REJECTED"),
            ("Private/pipe.md", "SPECIAL_FILE_REJECTED"),
            ("Private/plain.txt", "NOT_MARKDOWN"),
        ):
            with self.subTest(relative=relative), self.assertRaises(guard.GuardFailure) as caught:
                guard.resolve_vault_target(self.ctx, relative)
            self.assertEqual(caught.exception.code, code)

    def test_scan_vault_markdown_is_bounded_and_cannot_escape_the_vault(self) -> None:
        self.write_scope("captures/in-scope.md", "vault scan marker\n")
        (self.private / "matching.md").write_text("vault scan marker\n", encoding="utf-8")
        outside = Path(self.tempdir) / "outside"
        outside.mkdir()
        (outside / "escaped.md").write_text("vault scan marker\n", encoding="utf-8")
        os.symlink(outside, self.private / "escaped-directory")
        os.symlink(self.private / "matching.md", self.private / "matching-link.md")

        records = guard.scan_vault_markdown(self.ctx, "vault scan marker")
        self.assertEqual(
            [record.vault_relative_path for record in records],
            ["Mind Garden/captures/in-scope.md", "Private/matching.md"],
        )
        self.assertEqual(records[0].scope_relative_path, "captures/in-scope.md")
        self.assertIsNone(records[1].scope_relative_path)
        with self.assertRaises(guard.GuardFailure) as linked_read:
            guard.read_vault_markdown(self.ctx, "Private/matching-link.md")
        self.assertEqual(linked_read.exception.code, "SYMLINK_REJECTED")
        with self.assertRaises(guard.GuardFailure) as escaped_read:
            guard.resolve_vault_target(self.ctx, "Private/escaped-directory/escaped.md")
        self.assertEqual(escaped_read.exception.code, "SYMLINK_REJECTED")

        for kwargs in (
            {"max_files": 1},
            {"max_bytes": 1},
            {"max_matches": 1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(guard.GuardFailure) as bounded:
                guard.scan_vault_markdown(self.ctx, "vault scan marker", **kwargs)
            self.assertEqual(bounded.exception.code, "SCAN_LIMIT")

        entry_vault = Path(self.tempdir) / "Entry Cap Vault"
        entry_scope = entry_vault / "a-write-scope"
        entry_load = entry_vault / "z-entry-load"
        entry_scope.mkdir(parents=True)
        entry_load.mkdir()
        entry_ctx = guard.validate_scope_config({
            **self.data,
            "vault_path": str(entry_vault),
            "allowed_subdirectory": "a-write-scope",
        })
        for index in range(6):
            (entry_load / f"non-markdown-{index}.txt").write_text("ignored", encoding="utf-8")
        with mock.patch.object(guard, "MAX_SCAN_ENTRIES", 5):
            with self.assertRaises(guard.GuardFailure) as entry_limit:
                guard.scan_vault_markdown(entry_ctx, "no match")
        self.assertEqual(entry_limit.exception.code, "SCAN_LIMIT")

        (self.private / "invalid.md").write_bytes(b"\xff")
        with self.assertRaises(guard.GuardFailure) as invalid_utf8:
            guard.scan_vault_markdown(self.ctx, "vault scan marker")
        self.assertEqual(invalid_utf8.exception.code, "INVALID_UTF8")

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

    def test_explicit_legacy_content_note_rename_reads_back_and_removes_source(self) -> None:
        source_path = "captures/mg-20260914-044626.md"
        source = guard.exclusive_create(self.ctx, source_path, "legacy content\n")
        destination_path = "captures/Shoulder stability--mg-20260914-044626.md"

        renamed = guard.rename_content_note_expected(
            self.ctx, source_path, destination_path, source.sha256,
        )

        self.assertEqual(renamed.scope_relative_path, destination_path)
        self.assertEqual(renamed.vault_relative_path, f"Mind Garden/{destination_path}")
        self.assertEqual((renamed.text, renamed.sha256), (source.text, source.sha256))
        self.assertEqual(guard.read_markdown(self.ctx, destination_path), renamed)
        with self.assertRaises(guard.GuardFailure) as missing_source:
            guard.resolve_target(self.ctx, source_path)
        self.assertEqual(missing_source.exception.code, "NOT_FOUND")

    def test_explicit_legacy_content_note_rename_conflict_and_stale_hash_preserve_source(self) -> None:
        source_path = "developments/mg-20260914-044626.md"
        destination_path = "developments/Stable title--mg-20260914-044626.md"
        source = guard.exclusive_create(self.ctx, source_path, "legacy development\n")
        destination = guard.exclusive_create(self.ctx, destination_path, "existing development\n")

        with self.assertRaises(guard.GuardFailure) as conflict:
            guard.rename_content_note_expected(self.ctx, source_path, destination_path, source.sha256)
        self.assertEqual(conflict.exception.code, "ALREADY_EXISTS")
        self.assertEqual(guard.read_markdown(self.ctx, source_path), source)
        self.assertEqual(guard.read_markdown(self.ctx, destination_path), destination)

        untouched_destination = "developments/Fresh title--mg-20260914-044627.md"
        updated = guard.patch_expected(self.ctx, source_path, source.sha256, "updated legacy development\n")
        for stale_hash in (source.sha256, "A" * 64, "0" * 63, True, 1):
            with self.subTest(stale_hash=stale_hash), self.assertRaises(guard.GuardFailure) as stale:
                guard.rename_content_note_expected(self.ctx, source_path, untouched_destination, stale_hash)
            self.assertEqual(stale.exception.code, "HASH_CONFLICT")
        self.assertEqual(guard.read_markdown(self.ctx, source_path), updated)
        self.assertFalse((self.scope / untouched_destination).exists())

    def test_explicit_legacy_content_note_rename_rejects_invalid_paths_names_and_non_markdown(self) -> None:
        source_path = "captures/mg-20260914-044626.md"
        source = guard.exclusive_create(self.ctx, source_path, "legacy capture\n")
        canonical_destination = "captures/Readable title--mg-20260914-044626.md"
        self.write_scope("captures/nested/mg-20260914-044626.md", "nested\n")
        self.write_scope("review/mg-20260914-044626.md", "review\n")
        self.write_scope("arbitrary/mg-20260914-044626.md", "arbitrary\n")
        self.write_scope("captures/plain.txt", "not markdown\n")

        cases = (
            (source_path, "developments/Readable title--mg-20260914-044626.md", "PATH_INVALID"),
            ("review/mg-20260914-044626.md", canonical_destination, "PATH_INVALID"),
            ("arbitrary/mg-20260914-044626.md", canonical_destination, "PATH_INVALID"),
            ("captures/nested/mg-20260914-044626.md", canonical_destination, "PATH_INVALID"),
            (source_path, "captures/not-a-canonical-name.md", "PATH_INVALID"),
            (source_path, "captures/  Spaced title--mg-20260914-044626.md", "PATH_INVALID"),
            (source_path, "captures/Readable title--mg-not-an-id.md", "PATH_INVALID"),
            ("captures/plain.txt", canonical_destination, "NOT_MARKDOWN"),
            (source_path, "captures/Readable title--mg-20260914-044626.txt", "NOT_MARKDOWN"),
        )
        for from_path, to_path, code in cases:
            with self.subTest(from_path=from_path, to_path=to_path), self.assertRaises(guard.GuardFailure) as caught:
                guard.rename_content_note_expected(self.ctx, from_path, to_path, source.sha256)
            self.assertEqual(caught.exception.code, code)

        self.assertEqual(guard.read_markdown(self.ctx, source_path), source)
        self.assertFalse((self.scope / canonical_destination).exists())

    def test_explicit_legacy_content_note_rename_rejects_symlink_special_and_closes_descriptors(self) -> None:
        destination_path = "captures/Readable title--mg-20260914-044626.md"
        symlink_path = self.scope / "captures" / "mg-20260914-044626.md"
        os.symlink(self.private_note, symlink_path)
        with self.assertRaises(guard.GuardFailure) as symlink:
            guard.rename_content_note_expected(self.ctx, "captures/mg-20260914-044626.md", destination_path, "0" * 64)
        self.assertEqual(symlink.exception.code, "SYMLINK_REJECTED")
        self.assertTrue(symlink_path.is_symlink())
        symlink_path.unlink()

        fifo_path = self.scope / "captures" / "mg-20260914-044626.md"
        os.mkfifo(fifo_path)
        with self.assertRaises(guard.GuardFailure) as special:
            guard.rename_content_note_expected(self.ctx, "captures/mg-20260914-044626.md", destination_path, "0" * 64)
        self.assertEqual(special.exception.code, "SPECIAL_FILE_REJECTED")
        fifo_path.unlink()

        if os.path.isdir("/dev/fd"):
            source_path = "captures/mg-20260914-044627.md"
            source = guard.exclusive_create(self.ctx, source_path, "descriptor fixture\n")
            before = len(os.listdir("/dev/fd"))
            for _ in range(10):
                with self.assertRaises(guard.GuardFailure) as stale:
                    guard.rename_content_note_expected(
                        self.ctx,
                        source_path,
                        "captures/Descriptor check--mg-20260914-044627.md",
                        "0" * 64,
                    )
                self.assertEqual(stale.exception.code, "HASH_CONFLICT")
            self.assertEqual(len(os.listdir("/dev/fd")), before)
            self.assertEqual(guard.read_markdown(self.ctx, source_path), source)

    def test_raster_attachment_plan_read_and_bundle_are_content_addressed(self) -> None:
        fixtures = {
            "image/png": b"\x89PNG\r\n\x1a\nfixture-png",
            "image/jpeg": b"\xff\xd8\xfffixture-jpeg\xff\xd9",
            "image/webp": b"RIFF\x08\x00\x00\x00WEBPfixture",
        }
        plans = [guard.plan_raster_attachment(payload, media_type, 1024) for media_type, payload in fixtures.items()]
        self.assertFalse((self.scope / "attachments").exists())  # planning is pure in-memory work
        development = "# Images\n\n" + "\n".join(
            f"![[Mind Garden/{plan.target_scope_relative_path}]]" for plan in plans
        ) + "\n"
        result = guard.exclusive_create_development_bundle(
            self.ctx, "developments/mg-images.md", development, plans
        )
        self.assertEqual(result.status, "complete")
        self.assertIsNotNone(result.development)
        self.assertEqual(len(result.attachments), 3)
        for plan in plans:
            self.assertRegex(plan.target_scope_relative_path, r"^attachments/[0-9a-f]{64}\.(png|jpg|webp)$")
            record = guard.read_attachment(self.ctx, plan.target_scope_relative_path)
            self.assertEqual((record.sha256, record.media_type, record.byte_count), (plan.sha256, plan.media_type, len(plan.payload)))
            self.assertTrue((self.scope / plan.target_scope_relative_path).is_file())

    def test_raster_attachment_rejects_invalid_magic_mime_size_target_and_symlink(self) -> None:
        png = b"\x89PNG\r\n\x1a\nfixture"
        for payload, media_type, maximum in (
            (b"<svg></svg>", "image/png", 1024),
            (png, "image/jpeg", 1024),
            (png, "image/png", 1),
            (b"", "image/png", 1024),
        ):
            with self.subTest(media_type=media_type, maximum=maximum), self.assertRaises(guard.GuardFailure) as caught:
                guard.plan_raster_attachment(payload, media_type, maximum)
            self.assertEqual(caught.exception.code, "ATTACHMENT_INVALID")
        with self.assertRaises(guard.GuardFailure) as target:
            guard.read_attachment(self.ctx, "attachments/not-content-addressed.png")
        self.assertEqual(target.exception.code, "ATTACHMENT_INVALID")
        with self.assertRaises(guard.GuardFailure) as text_api:
            guard.exclusive_create(self.ctx, "attachments/not-allowed.md", "nope")
        self.assertEqual(text_api.exception.code, "PATH_INVALID")
        (self.scope / "attachments").mkdir()
        os.rmdir(self.scope / "attachments")
        os.symlink(self.private, self.scope / "attachments")
        plan = guard.plan_raster_attachment(png, "image/png", 1024)
        result = guard.exclusive_create_development_bundle(
            self.ctx, "developments/mg-link.md", f"# no\n\n![[Mind Garden/{plan.target_scope_relative_path}]]\n", [plan]
        )
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.failure_code, "SYMLINK_REJECTED")

    def test_bundle_reports_partial_orphans_and_never_deletes_on_development_conflict(self) -> None:
        guard.exclusive_create(self.ctx, "developments/mg-conflict.md", "already exists\n")
        plan = guard.plan_raster_attachment(b"\x89PNG\r\n\x1a\norphan", "image/png", 1024)
        result = guard.exclusive_create_development_bundle(
            self.ctx, "developments/mg-conflict.md", f"would be development\n\n![[Mind Garden/{plan.target_scope_relative_path}]]\n", [plan]
        )
        self.assertEqual(result.status, "partial")
        self.assertIsNone(result.development)
        self.assertEqual(result.failure_code, "ALREADY_EXISTS")
        self.assertEqual([item.target_scope_relative_path for item in result.orphaned_attachments], [plan.target_scope_relative_path])
        self.assertTrue((self.scope / plan.target_scope_relative_path).is_file())
        self.assertEqual(guard.read_attachment(self.ctx, plan.target_scope_relative_path).sha256, plan.sha256)
        self.assertEqual((self.scope / "developments" / "mg-conflict.md").read_text(encoding="utf-8"), "already exists\n")
    def test_bundle_rejects_every_nonplanned_active_embed_before_writes(self) -> None:
        plan = guard.plan_raster_attachment(b"\x89PNG\r\n\x1a\nembed", "image/png", 1024)
        legal = f"![[Mind Garden/{plan.target_scope_relative_path}]]"
        invalid_embeds = (
            "![[Other Garden/attachments/" + plan.target_scope_relative_path.split("/", 1)[1] + "]]",
            "![[Mind Garden/../../Private/secret.png]]",
            "![[https://example.test/image.png]]",
            "![[Mind Garden/attachments/not-a-hash.png]]",
            legal + "\n" + legal,
            legal + "\n![[Mind Garden/attachments/" + "0" * 64 + ".png]]",
            f"![[Mind Garden/{plan.target_scope_relative_path}|alias]]",
            f"![[Mind Garden/{plan.target_scope_relative_path}#anchor]]",
            legal + "\n![[Mind Garden/attachments/" + "0" * 64,
        )
        for number, text in enumerate(invalid_embeds):
            with self.subTest(text=text), self.assertRaises(guard.GuardFailure) as caught:
                guard.exclusive_create_development_bundle(self.ctx, f"developments/mg-invalid-{number}.md", text, [plan])
            self.assertEqual(caught.exception.code, "ATTACHMENT_INVALID")
            self.assertFalse((self.scope / "attachments").exists())
            self.assertFalse((self.scope / "developments" / f"mg-invalid-{number}.md").exists())
        literal = f"```text\n{legal}\n```\n"
        result = guard.exclusive_create_development_bundle(self.ctx, "developments/mg-literal.md", literal, [])
        self.assertEqual(result.status, "complete")
        self.assertFalse((self.scope / "attachments").exists())

    def test_bundle_ledger_reports_verified_and_potential_orphans_without_deletion(self) -> None:
        plan = guard.plan_raster_attachment(b"\x89PNG\r\n\x1a\nledger", "image/png", 1024)
        text = f"![[Mind Garden/{plan.target_scope_relative_path}]]\n"
        original_write = guard._write_all

        def write_then_fail(fd: int, payload: bytes) -> None:
            original_write(fd, payload)
            raise OSError("fixture failure")

        with mock.patch.object(guard, "_write_all", side_effect=write_then_fail):
            result = guard.exclusive_create_development_bundle(self.ctx, "developments/mg-write-fail.md", text, [plan])
        self.assertEqual((result.status, result.failure_code), ("partial", "ATTACHMENT_WRITE_FAILED"))
        self.assertEqual([item.target for item in result.orphans], [plan.target])
        self.assertEqual(result.potential_orphans, ())
        self.assertTrue((self.scope / plan.target).exists())

        synced = guard.plan_raster_attachment(b"RIFF\x08\x00\x00\x00WEBPledger-sync", "image/webp", 1024)
        synced_text = f"![[Mind Garden/{synced.target}]]\n"
        with mock.patch.object(guard.os, "fsync", side_effect=OSError("fixture sync failure")):
            fsync_result = guard.exclusive_create_development_bundle(self.ctx, "developments/mg-sync-fail.md", synced_text, [synced])
        self.assertEqual((fsync_result.status, fsync_result.failure_code), ("partial", "ATTACHMENT_WRITE_FAILED"))
        self.assertEqual([item.target for item in fsync_result.orphans], [synced.target])

        second = guard.plan_raster_attachment(b"\xff\xd8\xffledger-second", "image/jpeg", 1024)
        second_text = f"![[Mind Garden/{second.target}]]\n"
        with mock.patch.object(guard, "read_attachment", side_effect=guard.GuardFailure("NOT_FOUND")):
            potential = guard.exclusive_create_development_bundle(self.ctx, "developments/mg-read-fail.md", second_text, [second])
        self.assertEqual((potential.status, potential.failure_code), ("partial", "ATTACHMENT_WRITE_FAILED"))
        self.assertEqual(potential.orphans, ())
        self.assertEqual([item.target for item in potential.potential_orphans], [second.target])
        self.assertTrue((self.scope / second.target).exists())

    def test_bundle_two_plan_failure_keeps_earlier_and_later_orphan_identities(self) -> None:
        first = guard.plan_raster_attachment(b"\x89PNG\r\n\x1a\nfirst", "image/png", 1024)
        second = guard.plan_raster_attachment(b"\xff\xd8\xffsecond", "image/jpeg", 1024)
        text = "\n".join((f"![[Mind Garden/{first.target}]]", f"![[Mind Garden/{second.target}]]"))
        original_write = guard._write_all

        def fail_second(fd: int, payload: bytes) -> None:
            original_write(fd, payload)
            if payload == second.payload:
                raise OSError("fixture second failure")

        with mock.patch.object(guard, "_write_all", side_effect=fail_second):
            result = guard.exclusive_create_development_bundle(self.ctx, "developments/mg-two-fail.md", text, [first, second])
        self.assertEqual((result.status, result.failure_code), ("partial", "ATTACHMENT_WRITE_FAILED"))
        self.assertEqual([item.target for item in result.orphans], [first.target, second.target])
        self.assertEqual(result.potential_orphans, ())
        self.assertFalse((self.scope / "developments" / "mg-two-fail.md").exists())

    def test_bundle_reused_attachment_read_oserror_returns_partial_with_first_orphan(self) -> None:
        first = guard.plan_raster_attachment(b"\x89PNG\r\n\x1a\nreuse-first", "image/png", 1024)
        reused = guard.plan_raster_attachment(b"\xff\xd8\xffreuse-second", "image/jpeg", 1024)
        # Seed only the later plan, so the invocation must create the first
        # target before encountering the reused-attachment read fault.
        guard._exclusive_create_attachment_payload(self.ctx, reused)
        text = "\n".join((f"![[Mind Garden/{first.target}]]", f"![[Mind Garden/{reused.target}]]"))
        original_read = guard.read_attachment

        def fail_only_reused_read(ctx: guard.ScopeContext, target: str) -> guard.AttachmentRecord:
            if target == reused.target:
                raise OSError("fixture reused attachment read failure")
            return original_read(ctx, target)

        with mock.patch.object(guard, "read_attachment", side_effect=fail_only_reused_read):
            result = guard.exclusive_create_development_bundle(
                self.ctx, "developments/mg-reused-read-fail.md", text, [first, reused]
            )
        self.assertEqual((result.status, result.failure_code), ("partial", "ATTACHMENT_WRITE_FAILED"))
        self.assertIsNone(result.development)
        self.assertEqual([item.target for item in result.orphans], [first.target])
        self.assertEqual(result.potential_orphans, ())
        self.assertTrue((self.scope / first.target).is_file())
        self.assertTrue((self.scope / reused.target).is_file())
        self.assertFalse((self.scope / "developments" / "mg-reused-read-fail.md").exists())


if __name__ == "__main__":
    unittest.main()
