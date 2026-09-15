# Mind Garden artifact schema

## Layout and stable note types

All persistent Mind Garden artifacts live inside the configured
`allowed_subdirectory` (the configured write folder). Their paths are always
scope-relative to that configured folder; no artifact path hardcodes a folder name.
Source notes used for discovery, connections, development, distillation, or review may
live anywhere inside the configured Vault. A whole-Vault-only source is represented by
its Vault-relative path and has no writable `scope_relative_path`.

- `captures/<id>.md`
- `developments/<id>.md`
- `distillations/<id>.md`
- `review/Mind Garden Review.md` and (opt-in) `review/Mind Garden Review.base`
- `attachments/<lowercase-sha256>.png|.jpg|.webp` (raster-only, not Markdown)

`<id>` is a stable `mg-` identifier. If one listed direct parent is missing, an
exclusive create may create that fixed parent inside `allowed_subdirectory`. Reads
never initialize directories, and write APIs cannot address another Vault folder.
`move_expected` remains unsupported. Captures use frontmatter
`kind: mind-garden-capture`, `id`, `status: open`, and `created_at`; derived notes use
`kind: mind-garden-development` or `kind: mind-garden-distillation` and complete
Vault-relative `derived_from` paths.

## Literal capture invariant

A capture has an `## Original expression (literal; do not rewrite)` region enclosed
by a dynamic backtick fence longer than any run in the original input. The exact
input code points occur unchanged between the opening and closing fence. Pseudo
wikilinks and Markdown inside it are never interpreted, normalized, escaped, or
improved. `original_expression_digest` protects that entire region.

Two independently mutable regions can appear in a capture, development, or
distillation:

```text
<!-- mind-garden:development:start -->
... visibly attributed, append-only discussion entries ...
<!-- mind-garden:development:end -->

<!-- mind-garden:connections:start -->
... managed path-qualified links only ...
<!-- mind-garden:connections:end -->
```

`patch_managed_development` appends a labeled entry without changing earlier entries
or anything outside its markers. It preserves the user's contributed text literally
inside a dynamic fence and labels agent-authored interpretation separately.
`patch_managed_connections` replaces only the managed link list. Both operations
prove that a capture's Original expression digest is unchanged and produce an exact
unified diff before `patch_expected` uses the current SHA-256. Because they modify an
existing note, they must show the scope-relative target, relevant hashes, and that
diff and obtain fresh confirmation. Existing notes without the required region remain
readable but are not implicitly upgraded during a merge or connect operation.

## Links and provenance

Every generated internal link is Vault-root-relative, extensionless, and
path-qualified, and it may reference any unique note in the configured Vault. Link
target and display are independently validated/escaped. A derivative lists every
selected source, visible link, and SHA-256; source content outside
`allowed_subdirectory` is read-only. Missing, outside-Vault, ambiguous, bare,
abbreviated, embedded, and invalid-anchor links remain unresolved text.

## External development evidence and attachments

Only `development` may render structured external enrichment. For host-result states,
the `ExternalSearchRequest` independently retains the local query and fixed effective
cap; the host echo is comparison-only. The visible `External search query (derived
locally)` audit line therefore contains only that retained local query, never raw host
data. `offline` and `unavailable` contain no audit query. Existing callers that omit
enrichment use the exact legacy derivative bytes, including `### Agent contribution`
and all four public managed-marker constants.

A candidate attachment has declared media type, source URL, license, retrieval time,
byte count, and SHA-256. The guard accepts matching PNG/JPEG/WebP magic bytes only and
assigns its fixed content-addressed relative path; external filenames and URL paths do
not participate. The only active attachment grammar is the path-qualified internal
form `![[<configured allowed_subdirectory>/attachments/<lowercase-sha256>.<png|jpg|webp>]]`.
Here `<configured allowed_subdirectory>` denotes the actual user configuration, not a
literal folder name. Aliases, anchors, size suffixes, sibling paths, URLs,
malformed/unclosed embeds, duplicates, and planned-but-unembedded targets fail before
mutation. Literal fenced text is untrusted evidence, not an active embed.

`exclusive_create_development_bundle` validates all plans and active embeds before any
persistence, writes/reuses attachments first, creates the development last, and reads
participants back. Its attachment and development paths are scope-relative to
`allowed_subdirectory`. On partial failure it never deletes: `orphaned_attachments`
are proven guarded-read reusable records, while `potential_orphaned_attachments` are
identity-only plans that may have crossed `O_EXCL` but could not be verified. The latter
must never be reported as reusable content.

## Interaction policy, previews, and writes

A clear request for a new capture or new standalone development may create its new
scope-relative artifact through the guard and read it back without an extra preview or
confirmation round. The direct-create exception includes a validated attachment bundle
for that new standalone development.

An append or patch to an existing note, every connection operation, and any overwrite
or patch of review Markdown or Base must show the target, relevant current and
proposed SHA-256 hashes, and the exact unified diff, then obtain fresh confirmation
before the guarded write. A decline, hash conflict, or uncertain target leaves only an
unsaved artifact proposal. Creates use exclusive creation; existing-note patches use an
expected source hash; every successful write is immediately guarded-read and checked.
Every write target remains scope-relative to `allowed_subdirectory`.

Distillation is deliberately conservative. Even after its sources are uniquely
identified, show the complete source list with their Vault-relative paths and hashes,
the proposed scope-relative target, and the exact new-file diff; obtain fresh
confirmation before exclusive creation and read-back.

## Review projection

The Markdown snapshot is non-authoritative relative to source notes. It may list
matching captures discovered anywhere in the configured Vault, but the snapshot and
optional Base are written only as scope-relative paths inside
`allowed_subdirectory`. Overwriting or patching either review artifact follows the
confirmation policy above.
