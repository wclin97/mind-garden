from __future__ import annotations

import unittest

from fixtures import VaultFixture, guard


def _managed_region(text: str, start: str, end: str) -> str:
    return text[text.index(start) + len(start):text.index(end)]


class ArtifactTests(VaultFixture):
    def test_capture_preserves_literal_original_and_appends_managed_development(self) -> None:
        original = "\n  想法 😀 [[not a link]]\n````\ntrailing  \n"
        capture = guard.render_capture("mg-idea-1", original, "2026-09-13T00:00:00Z")
        self.assertIn(original, capture)
        self.assertIn("`````", capture)
        self.assertIn(guard.MANAGED_DEVELOPMENT_START, capture)
        self.assertIn(guard.MANAGED_CONNECTIONS_START, capture)
        before_digest = guard.original_expression_digest(capture)

        first = guard.patch_managed_development(
            capture, "user text\n````", "Agent keeps the question open.", "2026-09-13T00:01:00Z"
        )
        first_development = _managed_region(first, guard.MANAGED_DEVELOPMENT_START, guard.MANAGED_DEVELOPMENT_END)
        first_connections = _managed_region(first, guard.MANAGED_CONNECTIONS_START, guard.MANAGED_CONNECTIONS_END)
        self.assertIn("`````\nuser text\n````\n`````", first_development)
        self.assertIn("#### Agent development", first_development)
        self.assertEqual(before_digest, guard.original_expression_digest(first))

        second = guard.patch_managed_development(
            first, "second user contribution", "Second agent development.", "2026-09-13T00:02:00Z"
        )
        second_development = _managed_region(second, guard.MANAGED_DEVELOPMENT_START, guard.MANAGED_DEVELOPMENT_END)
        self.assertTrue(second_development.startswith(first_development))
        self.assertEqual(first_connections, _managed_region(second, guard.MANAGED_CONNECTIONS_START, guard.MANAGED_CONNECTIONS_END))
        self.assertEqual(before_digest, guard.original_expression_digest(second))

    def test_connections_support_all_artifact_kinds_and_legacy_notes_fail_closed(self) -> None:
        capture = guard.render_capture("mg-capture", "literal", "2026-09-13T00:00:00Z")
        source = guard.exclusive_create(self.ctx, "captures/mg-source.md", capture)
        artifacts = [
            capture,
            guard.render_derivative("development", "mg-development", "Development", "Consider the source.", [source], "2026-09-13T00:00:00Z"),
            guard.render_derivative("distillation", "mg-distillation", "Distillation", "Preserve the source.", [source], "2026-09-13T00:00:00Z"),
        ]
        link = "[[Mind Garden/captures/mg-source|source]]"
        for artifact in artifacts:
            with self.subTest(kind=guard._parse_frontmatter(artifact)["kind"]):
                before_development = _managed_region(artifact, guard.MANAGED_DEVELOPMENT_START, guard.MANAGED_DEVELOPMENT_END)
                before_digest = guard.original_expression_digest(artifact) if "capture" in artifact.split("\n", 3)[1] else None
                patched = guard.patch_managed_connections(artifact, [link])
                self.assertEqual(before_development, _managed_region(patched, guard.MANAGED_DEVELOPMENT_START, guard.MANAGED_DEVELOPMENT_END))
                self.assertIn(f"- {link}", patched)
                if before_digest is not None:
                    self.assertEqual(before_digest, guard.original_expression_digest(patched))

        legacy = (
            "---\nkind: mind-garden-capture\nid: mg-legacy\nstatus: open\n---\n\n"
            "## Original expression (literal; do not rewrite)\n\n```\nlegacy\n```\n\n"
            "<!-- mind-garden:connections:start -->\n<!-- mind-garden:connections:end -->\n"
        )
        for patch in (
            lambda: guard.patch_managed_development(legacy, "user", "agent", "2026-09-13T00:00:00Z"),
            lambda: guard.patch_managed_connections(legacy, [link]),
        ):
            with self.subTest(patch=patch), self.assertRaises(guard.GuardFailure) as caught:
                patch()
            self.assertEqual(caught.exception.code, "PATH_INVALID")

    def test_path_qualified_link_builder_escapes_display_and_rejects_bare_target(self) -> None:
        link = guard.build_wikilink("Mind Garden/captures/mg-a", "a | b]")
        self.assertEqual(link, "[[Mind Garden/captures/mg-a|a \\| b\\]]]" )
        with self.assertRaises(guard.GuardFailure):
            guard.build_wikilink("mg-a", "bare")
        with self.assertRaises(guard.GuardFailure):
            guard.build_wikilink("Mind Garden/captures/a.md", "extension")

    def test_derivative_has_visible_source_sha_provenance_and_managed_regions(self) -> None:
        source = guard.exclusive_create(self.ctx, "captures/mg-a.md", guard.render_capture("mg-a", "raw", "2026-09-13T00:00:00Z"))
        derived = guard.render_derivative("development", "mg-dev", "Development", "A considered expansion.", [source], "2026-09-13T00:00:00Z")
        self.assertIn("derived_from:", derived)
        self.assertIn(source.sha256, derived)
        self.assertIn("[[Mind Garden/captures/mg-a|captures/mg-a.md]]", derived)
        self.assertIn(guard.MANAGED_DEVELOPMENT_START, derived)
        self.assertIn(guard.MANAGED_CONNECTIONS_START, derived)

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
