from __future__ import annotations

import unittest

from fixtures import VaultFixture, guard


class ArtifactTests(VaultFixture):
    def test_capture_round_trips_unicode_whitespace_markdown_and_fence_runs(self) -> None:
        original = "\n  想法 😀 [[not a link]]\n````\ntrailing  \n"
        capture = guard.render_capture("mg-idea-1", original, "2026-09-13T00:00:00Z")
        self.assertIn(original, capture)
        self.assertIn("`````", capture)
        before = guard.original_expression_digest(capture)
        patched = guard.patch_managed_connections(capture, ["[[Mind Garden/captures/mg-other|other]]"])
        self.assertEqual(before, guard.original_expression_digest(patched))
        self.assertIn("- [[Mind Garden/captures/mg-other|other]]", patched)

    def test_path_qualified_link_builder_escapes_display_and_rejects_bare_target(self) -> None:
        link = guard.build_wikilink("Mind Garden/captures/mg-a", "a | b]")
        self.assertEqual(link, "[[Mind Garden/captures/mg-a|a \\| b\\]]]")
        with self.assertRaises(guard.GuardFailure):
            guard.build_wikilink("mg-a", "bare")
        with self.assertRaises(guard.GuardFailure):
            guard.build_wikilink("Mind Garden/captures/a.md", "extension")

    def test_derivative_has_visible_source_and_sha_provenance(self) -> None:
        source = guard.exclusive_create(self.ctx, "captures/mg-a.md", guard.render_capture("mg-a", "raw", "2026-09-13T00:00:00Z"))
        derived = guard.render_derivative("development", "mg-dev", "Development", "A considered expansion.", [source], "2026-09-13T00:00:00Z")
        self.assertIn("derived_from:", derived)
        self.assertIn(source.sha256, derived)
        self.assertIn("[[Mind Garden/captures/mg-a|captures/mg-a.md]]", derived)

    def test_link_resolution_rejects_external_bare_duplicate_and_missing_anchor(self) -> None:
        one = guard.exclusive_create(self.ctx, "captures/a.md", "# A\n[[Mind Garden/captures/b|b]]\n")
        two = guard.exclusive_create(self.ctx, "captures/b.md", "# B\n")
        notes = [one, two]
        self.assertEqual(guard.resolve_wikilink(self.ctx, one, "B", notes).state, "unresolved")
        self.assertEqual(guard.resolve_wikilink(self.ctx, one, "https://example.test/a", notes).state, "unresolved")
        self.assertEqual(guard.resolve_wikilink(self.ctx, one, "Mind Garden/captures/b#Absent", notes).state, "unresolved")
        self.assertEqual(guard.resolve_wikilink(self.ctx, one, "Mind Garden/captures/b", notes).state, "resolved")
        self.assertEqual([note.scope_relative_path for note in guard.backlinks(self.ctx, "captures/b.md", notes)], ["captures/a.md"])

    def test_preview_carries_diff_hashes_and_sources(self) -> None:
        source = guard.exclusive_create(self.ctx, "captures/a.md", "source\n")
        preview = guard.make_preview("developments/x.md", "after\n", "before\n", [source])
        self.assertIn("-before", preview.unified_diff)
        self.assertIn("+after", preview.unified_diff)
        self.assertEqual(preview.sources, (("captures/a.md", source.sha256),))


if __name__ == "__main__":
    unittest.main()
