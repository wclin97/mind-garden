# Mind Garden artifact schema

## Layout and stable note types

All persistent notes live inside the authorized scope under the supported
single-namespace-owner model. An uncooperative same-user process must not concurrently
rename or replace the scope, its ancestors, an in-scope directory, or a target leaf
during a guard operation because public POSIX APIs cannot enforce that hostile case:

- `captures/<id>.md`
- `developments/<id>.md`
- `distillations/<id>.md`
- `review/Mind Garden Review.md` and (opt-in) `review/Mind Garden Review.base`
- `attachments/<lowercase-sha256>.png|.jpg|.webp` (raster-only, not Markdown)

`<id>` is a stable `mg-` identifier. No mode deletes a note. If one listed direct
parent is missing, the confirmed exclusive create may create only that fixed parent
descriptor-relatively as part of the same operation. Preview resolution does not
create it, and reads/patches never initialize directories. `move_expected` is
compatibility-only and always fails closed because POSIX rename cannot atomically
compare the source hash. Captures use frontmatter `kind: mind-garden-capture`, `id`,
`status: open`, and `created_at`; derived notes use `kind: mind-garden-development`
or `kind: mind-garden-distillation` and complete `derived_from` paths. The routing
model prefers one evolving note per coherent topic: current unsaved context is folded
into one draft, then a clearly matching existing note is preferred, and a new capture
is created only for a durable distinct thought.

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
prove that a capture's Original expression digest is unchanged and emit a unified
diff before `patch_expected` uses the source SHA-256. Existing notes without the
required region remain readable but are not implicitly upgraded during a merge or
connect operation.

## Links and provenance

Every generated internal link is vault-root-relative, extensionless, and
path-qualified: `[[Mind Garden/captures/mg-123|display]]`. Link target and display
are independently validated/escaped. A derivative lists every selected source,
visible link, and SHA-256; source content is never overwritten. A confirmed
same-topic merge is not a new derivative: it appends one attributed entry to the
existing note's managed development region. Missing, external, ambiguous, bare,
abbreviated, embedded, and invalid-anchor links remain literal unresolved text.

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
form `![[Mind Garden/attachments/<lowercase-sha256>.<png|jpg|webp>]]` for the selected
scope; aliases, anchors, size suffixes, sibling paths, URLs, malformed/unclosed embeds,
duplicates, and planned-but-unembedded targets fail before mutation. Literal fenced
text is untrusted evidence, not an active embed.

`exclusive_create_development_bundle` validates all plans and active embeds before any
persistence, writes/reuses attachments first, creates the development last, and
reads participants back. On partial failure it never deletes: `orphaned_attachments`
are proven guarded-read reusable records, while `potential_orphaned_attachments` are
identity-only plans that may have crossed `O_EXCL` but could not be verified. The latter
must never be reported as reusable content.

## Preview and writes

`Preview` contains target, prior/proposed SHA-256, unified diff, source
path/SHA-256 pairs, and proposed text. Every save requires fresh confirmation.
Create uses exclusive creation; existing-note patches use an expected source hash;
every successful write is immediately guarded-read and checked. Moves are currently
unsupported rather than approximated with a non-atomic rename. A decline, conflict,
or uncertain write has only an unsaved artifact draft.

## Review projection

The Markdown snapshot is authoritative enough to review but explicitly
non-authoritative relative to source captures. It contains only in-scope open
captures with explicit metadata, not mtime-derived state. An optional Base is a
separate view with exact folder, `kind`, `status`, and `.md` filters; a Base failure
never changes a capture and leaves the Markdown fallback intact.
