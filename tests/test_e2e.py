from __future__ import annotations

import unittest

from fixtures import SKILL_ROOT, VaultFixture, guard


class EndToEndFixtureTests(VaultFixture):
    def test_all_five_modes_use_only_disposable_authorized_scope(self) -> None:
        # capture: no scan is necessary; literal text is persisted only by exclusive create.
        first_text = guard.render_capture("mg-one", "原始 idea 😀\n````\n", "2026-09-13T00:00:00Z")
        second_text = guard.render_capture("mg-two", "second thought", "2026-09-13T00:00:00Z")
        first = guard.exclusive_create(self.ctx, "captures/mg-one.md", first_text)
        second = guard.exclusive_create(self.ctx, "captures/mg-two.md", second_text)
        self.assertEqual(guard.original_expression_digest(first.text), guard.original_expression_digest(first_text))

        # connect: only the managed region changes under an expected hash.
        link = guard.build_wikilink("Mind Garden/captures/mg-two", "second thought")
        proposed = guard.patch_managed_connections(first.text, [link])
        connected = guard.patch_expected(self.ctx, first.scope_relative_path, first.sha256, proposed)
        self.assertEqual(guard.original_expression_digest(connected.text), guard.original_expression_digest(first.text))

        # develop and distill: separate derivative notes retain complete provenance.
        development = guard.render_derivative("development", "mg-dev", "Develop", "Explore both fragments.", [connected, second], "2026-09-13T00:00:00Z")
        developed = guard.exclusive_create(self.ctx, "developments/mg-dev.md", development)
        distillation = guard.render_derivative("distillation", "mg-distill", "Distill", "Keep the question open.", [connected, developed], "2026-09-13T00:00:00Z")
        guard.exclusive_create(self.ctx, "distillations/mg-distill.md", distillation)

        # review: bounded scan cannot see the private sibling, and fallback is written separately.
        captures = guard.scan_markdown(self.ctx, "mind-garden-capture")
        self.assertEqual({record.scope_relative_path for record in captures}, {"captures/mg-one.md", "captures/mg-two.md"})
        review = guard.render_review_snapshot(captures, "2026-09-13T00:00:00Z")
        review_record = guard.exclusive_create(self.ctx, "review/Mind Garden Review.md", review)
        self.assertIn("Non-authoritative", review_record.text)
        self.assertNotIn("confidential", review_record.text)

    def test_proposes_only_strong_bounded_local_connections_after_save(self) -> None:
        source = guard.exclusive_create(
            self.ctx,
            "captures/mg-source.md",
            guard.render_capture("mg-source", "Resilient orchestration improves incident recovery.", "2026-09-13T00:00:00Z"),
        )
        strong = guard.exclusive_create(
            self.ctx,
            "captures/mg-strong.md",
            guard.render_capture("mg-strong", "Incident recovery needs resilient orchestration.", "2026-09-13T00:00:00Z"),
        )
        weak = guard.exclusive_create(
            self.ctx,
            "captures/mg-weak.md",
            guard.render_capture("mg-weak", "Resilient gardening catalog.", "2026-09-13T00:00:00Z"),
        )

        proposals = guard.propose_strong_connections(source, [source, weak, strong], max_candidates=99)
        self.assertLessEqual(len(proposals), 3)
        self.assertEqual([proposal.target_scope_relative_path for proposal in proposals], ["captures/mg-strong.md"])
        proposal = proposals[0]
        self.assertEqual(proposal.source_sha256, source.sha256)
        self.assertEqual(proposal.target_sha256, strong.sha256)
        self.assertIn("incident", proposal.reason)
        self.assertIn("+", proposal.unified_diff)
        self.assertIn(proposal.connection_link, proposal.proposed_text)
        self.assertEqual(guard.read_markdown(self.ctx, source.scope_relative_path).sha256, source.sha256)

        link = guard.build_wikilink(strong.vault_relative_path[:-3], "related recovery")
        proposed_text = guard.patch_managed_connections(source.text, [link])
        preview = guard.make_preview(source.scope_relative_path, proposed_text, source.text, [source, strong])
        self.assertIn("+", preview.unified_diff)
        self.assertEqual(preview.sources, ((source.scope_relative_path, source.sha256), (strong.scope_relative_path, strong.sha256)))

    def test_negative_paths_links_vendor_and_stale_write_return_safe_failures(self) -> None:
        record = guard.exclusive_create(self.ctx, "captures/a.md", guard.render_capture("mg-a", "raw", "2026-09-13T00:00:00Z"))
        for raw in ("Private/secret", "a", "https://example.test", "Mind Garden/captures/a#missing"):
            self.assertNotEqual(guard.resolve_wikilink(self.ctx, record, raw, [record]).state, "resolved")
        self.write_scope("captures/a.md", "concurrent replacement\n")
        with self.assertRaises(guard.GuardFailure) as stale:
            guard.patch_expected(self.ctx, "captures/a.md", record.sha256, "would overwrite\n")
        self.assertEqual(stale.exception.code, "HASH_CONFLICT")
        self.assertTrue(guard.verify_vendor(str(SKILL_ROOT))["ok"])

    def test_base_is_opt_in_data_and_markdown_fallback_survives(self) -> None:
        fallback = guard.render_review_snapshot([], "2026-09-13T00:00:00Z")
        base = guard.render_review_base("Mind Garden")
        self.assertIn("Non-authoritative", fallback)
        self.assertIn("file.inFolder", base)
        self.assertNotIn("captures/", base)  # filter is scope-based, not a whole-Vault path list


if __name__ == "__main__":
    unittest.main()
