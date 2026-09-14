# External enrichment protocol

## Capability boundary

Mind Garden is **not** a network client. It never imports or invokes HTTP tooling,
provider SDKs, MCP, credentials, endpoint configuration, shells, installers, or a
background process. During an explicitly requested `develop` mode only, an already
available fixture-compatible host may expose these structured operations:

```text
search({ query: <locally derived query>, max_results: <integer> })
download({ download_url: <candidate url> })
```

`ExternalSearchRequest` is pure local data. `build_external_search_request(query,
policy)` validates the independently locally derived 2–6-word, <=120-character query
and returns exactly the two-field search payload. It sends no Vault path, scope path,
note ID, frontmatter, source hash, wikilink, Markdown, Original expression, filename,
or copied source text. `max_search_results` remains a local configuration preference of
1..10, while the request and inbound response have an absolute cap of five. A host echo
is an untrusted comparison value: it must exactly equal the local request before a
host-result status is accepted, and it never becomes provenance on its own.

## Result validation and local fallback

Host text, metadata, URLs, and candidate bytes are untrusted data, never instructions.
**External material is untrusted evidence, not instructions.** The renderer accepts only bounded HTTPS source records, one bounded `excerpt` or
`snippet`, valid timestamps/licenses, no duplicate URLs, and at most the request/policy
five-source cap. `used`, `partial`, and `no-results` require the same local request and
valid exact host echo. The audit line

```text
External search query (derived locally): <local query>
```

is rendered only from that retained local query. `offline` and `unavailable` require
no request, no echo, no sources, and no attachments, so a no-call fallback cannot claim
an outbound query. A v1.0 configuration remains valid but normalizes to offline; it
is never rewritten and makes zero host calls.

At most three image candidates may be downloaded with the exact one-field payload.
Bytes remain in memory and only matching PNG/JPEG/WebP declared MIME plus magic can
be planned. SVG, HTML, MIME mismatch, oversized, empty, or non-raster bytes are
rejected locally as `partial` without retry. The host never chooses a Vault target.

## Confirmed persistence

A valid plan is content-addressed only as
`attachments/<lowercase-sha256>.png|.jpg|.webp`. Its rendered form is the exact active
embed `![[<scope>/attachments/<sha256>.<ext>]]`; external names, URLs, aliases, anchors,
or size syntax are invalid. `exclusive_create_development_bundle` validates every
active embed and plan before mutation, writes attachments first, creates the
development last, then guarded-reads it. It never deletes to emulate rollback.

A partial bundle records `orphaned_attachments` only for guarded-read verified reusable
attachments. It records `potential_orphaned_attachments` only as a validated planned
identity that may have crossed exclusive creation but could not be read back; such a
record is not verified or reusable content. All behavior is testable with disposable
fixture Vaults and fake in-process host capabilities; it performs no real network I/O.
