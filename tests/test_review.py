from __future__ import annotations

import unittest

from fixtures import VaultFixture, guard


class ReviewTests(VaultFixture):
    def test_empty_review_has_safe_markdown_fallback(self) -> None:
        rendered = guard.render_review_snapshot([], "2026-09-13T00:00:00Z")
        self.assertIn("Non-authoritative", rendered)
        self.assertIn("No open in-scope captures", rendered)

    def test_review_uses_only_explicit_open_capture_metadata(self) -> None:
        open_capture = guard.exclusive_create(self.ctx, "captures/open.md", guard.render_capture("mg-open", "keep", "2026-09-13T00:00:00Z"))
        closed = guard.exclusive_create(self.ctx, "captures/closed.md", "---\nkind: mind-garden-capture\nstatus: closed\n---\n# Closed\n")
        malformed = guard.exclusive_create(self.ctx, "captures/malformed.md", "---\nnot yaml\n# Missing close\n")
        rendered = guard.render_review_snapshot([open_capture, closed, malformed], "2026-09-13T00:00:00Z")
        self.assertIn("Mind Garden/captures/open", rendered)
        self.assertNotIn("closed", rendered)
        self.assertNotIn("malformed", rendered)

    def test_base_is_scope_filtered_and_yaml_safe_for_folder_characters(self) -> None:
        rendered = guard.render_review_base("Mind Garden/Ideas: special")
        self.assertIn("file.inFolder(\"Mind Garden/Ideas: special\")", rendered)
        self.assertIn('file.ext == "md"', rendered)
        self.assertIn('kind == "mind-garden-capture"', rendered)
        self.assertIn('status == "open"', rendered)
        self.assertNotIn("mtime", rendered)
        saved = guard.exclusive_create_text(self.ctx, "review/Mind Garden Review.base", rendered)
        self.assertEqual(saved.text, rendered)
        updated = guard.patch_expected_text(self.ctx, "review/Mind Garden Review.base", saved.sha256, rendered + "# manual render required\n")
        self.assertIn("manual render required", updated.text)

    def test_review_does_not_need_last_reviewed_or_infer_urgency(self) -> None:
        record = guard.exclusive_create(self.ctx, "captures/a.md", guard.render_capture("mg-a", "original", "2026-09-13T00:00:00Z"))
        rendered = guard.render_review_snapshot([record], "2026-09-13T00:00:00Z")
        self.assertNotIn("last_reviewed", rendered)
        self.assertNotIn("urgency", rendered.lower())


if __name__ == "__main__":
    unittest.main()
