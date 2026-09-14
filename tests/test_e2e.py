from __future__ import annotations

import unittest

from tests.fixtures import SKILL_ROOT, VaultFixture, guard


class RecordingFakeHostCapabilities:
    """Fixture-only host capability: it records narrow envelopes and performs no I/O."""

    def __init__(
        self, search_result: dict[str, object] | Exception, downloads: dict[str, tuple[str, bytes]] | None = None,
    ) -> None:
        self.search_result = search_result
        self.downloads = downloads or {}
        self.search_calls: list[dict[str, object]] = []
        self.download_calls: list[dict[str, object]] = []

    def search(self, payload: dict[str, object]) -> dict[str, object]:
        if set(payload) != {"query", "max_results"} or not isinstance(payload["query"], str) or not isinstance(payload["max_results"], int):
            raise AssertionError("invalid fixture search envelope")
        self.search_calls.append(dict(payload))
        if isinstance(self.search_result, Exception):
            raise self.search_result
        return dict(self.search_result)

    def download(self, payload: dict[str, object]) -> tuple[str, bytes]:
        if set(payload) != {"download_url"} or not isinstance(payload["download_url"], str):
            raise AssertionError("invalid fixture download envelope")
        self.download_calls.append(dict(payload))
        return self.downloads[payload["download_url"]]


def run_fixture_enrichment_flow(
    ctx: guard.ScopeContext, host: RecordingFakeHostCapabilities, locally_derived_query: str,
) -> tuple[dict[str, object], guard.ExternalSearchRequest | None]:
    """Test-only orchestration boundary; offline returns before host capabilities."""
    policy = ctx.external_enrichment
    if policy.mode == "offline":
        return {"status": "offline", "derived_query": None, "sources": [], "attachments": []}, None
    request = guard.build_external_search_request(locally_derived_query, policy)
    try:
        return host.search(request.as_host_payload()), request
    except RuntimeError:
        # A host failure is distinct from the policy-selected offline fallback.
        return {"status": "unavailable", "derived_query": None, "sources": [], "attachments": []}, None


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

        # develop and distill: same-topic context can stay in one note; separate
        # derivatives retain complete provenance when they are warranted.
        merged_text = guard.patch_managed_development(
            connected.text,
            "more context for the same idea",
            "Keep this discussion with the original thought.",
            "2026-09-13T00:30:00Z",
        )
        merged = guard.patch_expected(self.ctx, connected.scope_relative_path, connected.sha256, merged_text)
        self.assertIn("more context for the same idea", merged.text)
        development = guard.render_derivative("development", "mg-dev", "Develop", "Explore both fragments.", [merged, second], "2026-09-13T01:00:00Z")
        developed = guard.exclusive_create(self.ctx, "developments/mg-dev.md", development)
        distillation = guard.render_derivative("distillation", "mg-distill", "Distill", "Keep the question open.", [merged, developed], "2026-09-13T02:00:00Z")
        distilled = guard.exclusive_create(self.ctx, "distillations/mg-distill.md", distillation)
        related = guard.build_wikilink("Mind Garden/developments/mg-dev", "development")
        proposed_distillation = guard.patch_managed_connections(distilled.text, [related])
        connected_distillation = guard.patch_expected(
            self.ctx, distilled.scope_relative_path, distilled.sha256, proposed_distillation
        )
        self.assertIn("Mind Garden/developments/mg-dev", connected_distillation.text)

        # review: bounded scan cannot see the private sibling, and fallback is written separately.
        captures = guard.scan_markdown(self.ctx, "mind-garden-capture")
        self.assertEqual({record.scope_relative_path for record in captures}, {"captures/mg-one.md", "captures/mg-two.md"})
        review = guard.render_review_snapshot(captures, "2026-09-13T00:00:00Z")
        review_record = guard.exclusive_create(self.ctx, "review/Mind Garden Review.md", review)
        self.assertIn("Non-authoritative", review_record.text)
        self.assertNotIn("confidential", review_record.text)

    def test_recording_host_protocol_has_bounded_private_envelopes_and_local_fallbacks(self) -> None:
        source = guard.exclusive_create(
            self.ctx, "captures/mg-host.md", guard.render_capture("mg-host", "local only", "2026-09-14T00:00:00Z")
        )
        policy_ten = guard.ExternalEnrichmentPolicy("automatic", 10, 3, 1024, 500)
        request = guard.build_external_search_request("mind garden evidence", policy_ten)
        exact = {
            "status": "used", "derived_query": request.locally_derived_query,
            "sources": [{
                "source_url": "https://example.test/source", "title": "Fixture source",
                "excerpt": "A bounded external viewpoint.", "license": "unknown",
                "retrieved_at": "2026-09-14T00:00:00Z",
            }], "attachments": [],
        }
        host = RecordingFakeHostCapabilities(exact, {
            "https://example.test/one": ("image/png", b"\x89PNG\r\n\x1a\n1"),
            "https://example.test/two": ("image/jpeg", b"\xff\xd8\xff2"),
            "https://example.test/three": ("image/webp", b"RIFF\x08\x00\x00\x00WEBP3"),
            "https://example.test/four": ("image/png", b"<svg>not raster</svg>"),
        })
        response = host.search(request.as_host_payload())
        rendered = guard.render_derivative(
            "development", "mg-used", "Host result", "Local development stays available.",
            [source], "2026-09-14T00:00:01Z", response, policy_ten, search_request=request,
        )
        self.assertEqual(host.search_calls, [{"query": "mind garden evidence", "max_results": 5}])
        serialized_request = repr(host.search_calls[0])
        for forbidden in (str(self.vault), "Mind Garden", "mg-host", "frontmatter", "sha256", "[[", "local only"):
            self.assertNotIn(forbidden, serialized_request)
        self.assertIn("External search query (derived locally): mind garden evidence", rendered)
        self.assertIn("Fixture source", rendered)

        mismatch = {**exact, "derived_query": "other local evidence"}
        with self.assertRaises(guard.GuardFailure):
            guard.validate_external_enrichment(mismatch, policy=policy_ten, search_request=request)
        six_sources = [
            {**exact["sources"][0], "source_url": f"https://example.test/{number}"} for number in range(6)
        ]
        with self.assertRaises(guard.GuardFailure):
            guard.validate_external_enrichment({**exact, "sources": six_sources}, policy=policy_ten, search_request=request)

        # The fixture harness intentionally chooses no more than the production local cap.
        plans = []
        for url in ("https://example.test/one", "https://example.test/two", "https://example.test/three"):
            declared_mime, payload = host.download({"download_url": url})
            plans.append(guard.plan_raster_attachment(payload, declared_mime, 1024))
        self.assertEqual(len(host.download_calls), 3)
        self.assertEqual([set(call) for call in host.download_calls], [{"download_url"}] * 3)
        declared_mime, invalid_payload = host.downloads["https://example.test/four"]
        with self.assertRaises(guard.GuardFailure):
            guard.plan_raster_attachment(invalid_payload, declared_mime, 1024)
        partial = {**exact, "status": "partial", "attachments": []}
        self.assertEqual(guard.validate_external_enrichment(partial, policy=policy_ten, search_request=request).status, "partial")
        self.assertEqual(len(plans), 3)

        no_results = {"status": "no-results", "derived_query": request.locally_derived_query, "sources": [], "attachments": []}
        self.assertEqual(guard.validate_external_enrichment(no_results, policy=policy_ten, search_request=request).status, "no-results")

        record = guard.exclusive_create(self.ctx, "captures/a.md", guard.render_capture("mg-a", "raw", "2026-09-13T00:00:00Z"))
        for raw in ("Private/secret", "a", "https://example.test", "Mind Garden/captures/a#missing"):
            self.assertNotEqual(guard.resolve_wikilink(self.ctx, record, raw, [record]).state, "resolved")
        self.write_scope("captures/a.md", "concurrent replacement\n")
        with self.assertRaises(guard.GuardFailure) as stale:
            guard.patch_expected(self.ctx, "captures/a.md", record.sha256, "would overwrite\n")
        self.assertEqual(stale.exception.code, "HASH_CONFLICT")
        self.assertTrue(guard.verify_vendor(str(SKILL_ROOT))["ok"])

    def test_recording_host_explicit_and_legacy_offline_flows_make_zero_calls(self) -> None:
        source = guard.exclusive_create(
            self.ctx, "captures/mg-offline-source.md", guard.render_capture("mg-offline-source", "local", "2026-09-14T00:00:00Z")
        )
        explicit_data = {
            **self.data,
            "external_enrichment": {**self.data["external_enrichment"], "mode": "offline"},
        }
        legacy_data = {
            "schema_version": guard.LEGACY_CONFIG_VERSION,
            "vault_path": str(self.vault),
            "allowed_subdirectory": "Mind Garden",
        }
        contexts = (
            ("explicit", guard.validate_scope_config(explicit_data)),
            ("legacy", guard.validate_scope_config(legacy_data)),
        )
        for label, context in contexts:
            with self.subTest(mode=label):
                host = RecordingFakeHostCapabilities(RuntimeError("fixture host must remain unused"))
                fallback, request = run_fixture_enrichment_flow(context, host, "mind garden evidence")
                self.assertIsNone(request)
                self.assertEqual(guard.validate_external_enrichment(fallback, policy=context.external_enrichment).status, "offline")
                rendered = guard.render_derivative(
                    "development", f"mg-offline-{label}", "Offline", "Local", [source],
                    "2026-09-14T00:00:01Z", fallback, context.external_enrichment,
                )
                self.assertNotIn("External search query", rendered)
                self.assertEqual(host.search_calls, [])
                self.assertEqual(host.download_calls, [])

    def test_recording_host_unavailable_flow_is_not_offline(self) -> None:
        host = RecordingFakeHostCapabilities(RuntimeError("fixture host unavailable"))
        fallback, request = run_fixture_enrichment_flow(self.ctx, host, "mind garden evidence")
        self.assertIsNone(request)
        self.assertEqual(guard.validate_external_enrichment(fallback, policy=self.ctx.external_enrichment).status, "unavailable")
        self.assertEqual(host.search_calls, [{"query": "mind garden evidence", "max_results": 5}])
        self.assertEqual(host.download_calls, [])

    def test_base_is_opt_in_data_and_markdown_fallback_survives(self) -> None:
        fallback = guard.render_review_snapshot([], "2026-09-13T00:00:00Z")
        base = guard.render_review_base("Mind Garden")
        self.assertIn("Non-authoritative", fallback)
        self.assertIn("file.inFolder", base)
        self.assertNotIn("captures/", base)  # filter is scope-based, not a whole-Vault path list


if __name__ == "__main__":
    unittest.main()
