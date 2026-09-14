# Mind Garden artifact schema

## Layout and stable note types

All persistent notes live inside the authorized scope only:

- `captures/<id>.md`
- `developments/<id>.md`
- `distillations/<id>.md`
- `review/Mind Garden Review.md` and (opt-in) `review/Mind Garden Review.base`

`<id>` is a stable `mg-` identifier. No mode deletes a note. Captures use frontmatter
`kind: mind-garden-capture`, `id`, `status: open`, and `created_at`; derived notes
use `kind: mind-garden-development` or `kind: mind-garden-distillation` and complete
`derived_from` paths.

## Literal capture invariant

A capture has an `## Original expression (literal; do not rewrite)` region enclosed
by a dynamic backtick fence longer than any run in the original input. The exact
input code points occur unchanged between the opening and closing fence. Pseudo
wikilinks and Markdown inside it are never interpreted, normalized, escaped, or
improved. `original_expression_digest` protects that entire region.

The only mutable region in a capture is exactly:

```text
<!-- mind-garden:connections:start -->
... managed path-qualified links only ...
<!-- mind-garden:connections:end -->
```

`patch_managed_connections` proves that the Original expression digest is unchanged
and emits a unified diff before `patch_expected` uses the source SHA-256.

## Links and provenance

Every generated internal link is vault-root-relative, extensionless, and
path-qualified: `[[Mind Garden/captures/mg-123|display]]`. Link target and display
are independently validated/escaped. A derivative lists every selected source,
visible link, and SHA-256; source content is never overwritten. Missing, external,
ambiguous, bare, abbreviated, embedded, and invalid-anchor links remain literal
unresolved text.

## Preview and writes

`Preview` contains target, prior/proposed SHA-256, unified diff, source
path/SHA-256 pairs, and proposed text. Every save requires fresh confirmation.
Create uses exclusive creation; existing notes/moves use expected source hash; every
successful write is immediately guarded-read and checked. A decline, conflict, or
uncertain write has only an unsaved artifact draft.

## Review projection

The Markdown snapshot is authoritative enough to review but explicitly
non-authoritative relative to source captures. It contains only in-scope open
captures with explicit metadata, not mtime-derived state. An optional Base is a
separate view with exact folder, `kind`, `status`, and `.md` filters; a Base failure
never changes a capture and leaves the Markdown fallback intact.
