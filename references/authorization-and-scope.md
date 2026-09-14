# Authorization and scope

## Authorization state

The runtime authority is a machine-local configuration file selected only after the
user confirms both `vault_path` and `allowed_subdirectory`. The resolution order is
an absolute `MIND_GARDEN_CONFIG` file, an absolute
`$XDG_CONFIG_HOME/mind-garden/config.json`, then
`~/.config/mind-garden/config.json`. A relative override or XDG root is invalid. The
scope must be a strict descendant of the canonical Vault root. The Vault root itself
is never a valid scope.

When the local config is missing or invalid, return `CONFIG_MISSING` or
`CONFIG_INVALID` plus a configuration prompt/unsaved draft. Do not probe a focused
Vault, active file, home directory, environment setting, or example placeholder.

## Guard API

All Vault I/O must pass through `scripts/scope_guard.py`:

- `load_config()` and `validate_scope_config(data, allow_create_scope)`
- `resolve_target(ctx, scope_relative_path, purpose, allow_missing_leaf)`
- `scan_markdown(ctx, query, max_files, max_bytes, max_matches)` and
  `read_markdown(ctx, path)`
- `resolve_wikilink(ctx, source, raw, known_notes)` and `backlinks(...)`
- `exclusive_create` and `exclusive_create_text` may initialize only a missing direct
  parent in the fixed text set `captures`, `developments`, `distillations`, and `review`
- `plan_raster_attachment(payload, declared_mime, max_bytes)` validates only in-memory
  PNG/JPEG/WebP bytes and deterministically plans `attachments/<sha256>.<ext>`
- `ExternalSearchRequest`, `build_external_search_request(query, policy)`, and
  `ExternalSearchRequest.as_host_payload()` are pure no-I/O request validation; the
  payload has exactly local `query` and capped `max_results` fields
- `validate_external_enrichment(..., search_request=...)` binds host-result provenance
  to that independently retained local request
- `read_attachment(ctx, target)` reads only content-addressed matching raster bytes;
  text create/patch APIs cannot use `attachments`
- `exclusive_create_development_bundle(ctx, development_path, development_text, attachments)`
  validates every active embed before mutation, writes/reuses rasters, creates the
  development last, and reports verified orphan attachments or potential (unverified)
  orphan identities without deletion
- **Guard-only persistence:** no host result, normal conversation, or model judgment
  bypasses these guarded create/patch routes or the explicit mode/source/preview/
  confirmation boundary
- `patch_expected` / `patch_expected_text` for confirmed existing artifacts
- `move_expected` is compatibility-only and always returns `UNSUPPORTED_SAFE_IO`

The guard uses canonical realpath validation before each operation plus
POSIX `O_NOFOLLOW`/`O_DIRECTORY`, descriptor-relative `lstat`/`fstat`, regular-file
checks, and read-back hash verification. A confirmed exclusive create may use
descriptor-relative `mkdir` only for one missing fixed direct artifact parent, then
opens the complete `parent/leaf` path from a fresh scope-root descriptor with
component-wide `O_NOFOLLOW_ANY`; absence of that capability returns
`UNSUPPORTED_SAFE_IO` with no fallback. Preview resolution, reads, scans, and patches
never create directories. `move_expected` also returns `UNSUPPORTED_SAFE_IO` because
POSIX rename cannot atomically require an expected source hash. During an operation,
an uncooperative same-user process must not concurrently rename or replace the
configured scope, its ancestors, any directory inside the authorized scope tree
(including artifact parents), or the target leaf; public POSIX APIs cannot enforce
that hostile namespace boundary. Other unsupported trusted semantics likewise fail
closed.

## Scope semantics

A path must be nonempty POSIX scope-relative components. Reject absolute POSIX,
drive, UNC/device, backslash, NUL, `.`, `..`, symlinks, and special files. The
scanner recurses only through descriptor-proven directories under the canonical
scope, does not follow links, and obeys file/byte/match caps. Outside notes never
appear in a result or failure diagnostic.

Generated wikilinks name a unique already-scanned target by vault-root-relative,
extensionless, path-qualified path. Links that are bare titles, aliases, embeds,
URLs, scope-external paths, duplicate targets, malformed paths, or invalid anchors
remain unresolved. They cannot affect associations, backlinks, or review.

## External boundary

The only permitted outbound enrichment shape is the host-provided structured search
request described in [external-enrichment.md](external-enrichment.md): a locally
derived 2–6 word query (maximum 120 characters) plus a numeric result cap. No Vault
path, filename, note ID, frontmatter, source hash, wikilink, Markdown, Original
expression, or long copied note fragment crosses that boundary. The host is not a
Vault authority: its URLs and metadata never become filesystem targets.

Incoming source text and candidate bytes are untrusted. The guard accepts only
validated bounded HTTPS metadata and raster content-addressed paths. It does not
parse, execute, or upload external content; all Vault persistence still flows through
this guard and still requires the normal confirmed preview.
