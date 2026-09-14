# Mode protocols

## Explicit authorization and common sequence

A normal conversation, model judgment, keyword, or inferred topic never authorizes
Vault I/O. Begin only after a **specific explicit mode request** (`capture`, `develop`,
`connect`, `distill`, or `review`) identifies the mode and the required explicitly
selected, path-qualified in-scope source/target records. `capture` uses only the
supplied literal expression and a proposed new target. Never infer a source, target,
same-topic append, scan, retrieval, patch, or connection candidate from conversation
text.

Each requested mode loads the exact local vendor contracts, verifies the offline
manifest, loads the local scope through the guard, computes an unsaved draft, previews
it, and obtains a fresh confirmation. Preview target resolution never creates
directories. After confirmation, the same exclusive-create call may initialize only a
missing direct fixed artifact parent (`captures`, `developments`, `distillations`, or
`review`); reads/patches never initialize directories. Creation requires component-wide
`O_NOFOLLOW_ANY` and has no weaker fallback. `move_expected` always fails closed
because POSIX rename cannot atomically enforce an expected source hash.

Every operation displays selected sources and hashes, target, limits, exact draft (and
a unified diff for edits or multi-source output), then requires fresh confirmation.
Configuration, vendor, scope, confirmation, stale-source, target, or host failure
returns a non-leaking unsaved draft and never auto-retries.

## capture

Only an explicit `capture` request can create `captures/<id>.md`. Preserve the supplied
Original expression exactly in a dynamic literal fence, preview it, confirm, guarded
exclusive-create, and read it back. A normal conversation does not itself trigger a
scan, read, or capture.

## develop

A `develop` request supplies explicitly selected source records and, for an append, an
explicitly selected in-scope target. The exact append/new-derivative preview and fresh
confirmation remain mandatory. Automatic enrichment is develop-only and happens only
after that mode/source gate; it grants no separate source selection, Vault-read, or
connection authority.

For a v1.1 `automatic` policy, build one local `ExternalSearchRequest` from a safe
2–6-word query. Its only host payload is exactly `{query, max_results}`. Configuration
may express `max_search_results: 1..10`, but every host request and inbound result is
hard-capped at five; a lower request cap remains binding. The host echo is only checked
against the locally retained query and never supplies audit provenance. `used`,
`partial`, and `no-results` require that same request; `offline` and `unavailable` are
no-call shapes with no audit query. No other mode invokes a host capability.

Consider at most three raster candidates. Every `download` payload has exactly
`{download_url}`; bytes stay in memory until preview confirmation and must pass
PNG/JPEG/WebP matching MIME and magic validation. Invalid, oversized, or failed bytes
produce local `partial` with no retry. The confirmed bundle validates every active
embed before mutation, writes/reuses content-addressed attachments first, creates the
development last, and guarded-reads participants. A partial result distinguishes
verified reusable `orphaned_attachments` from identity-only
`potential_orphaned_attachments`; it never deletes either target.

## connect

Only an explicit `connect` request naming selected path-qualified in-scope source and
target records may proceed. Resolve only those records, preview the exact
managed-region diff and hashes, obtain fresh confirmation, use `patch_expected`, and
read back. Do not search for candidates or append a connection from a normal
conversation.

## distill

Use only explicitly selected sources. Preview a separate `distillations/<id>.md` with
complete provenance and source hashes, confirm, exclusive-create, and verify read-back.
Never reduce, delete, or revise a source capture.

## review

Only the explicit `review` mode may perform a bounded scan of authorized in-scope
Markdown captures whose frontmatter says `kind: mind-garden-capture` and `status: open`.
Preview/confirm a non-authoritative Markdown snapshot or an explicitly chosen Base,
then use the guard and retain the Markdown fallback if Base rendering is unverified.
