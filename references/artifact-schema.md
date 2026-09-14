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

`<id>` is a stable `mg-` identifier. No mode deletes a note. If one listed direct
parent is missing, the confirmed exclusive create may create only that fixed parent
descriptor-relatively as part of the same operation. Preview resolution does not
create it, and reads/patches never initialize directories. `move_expected` is
compatibility-only and always fails closed because POSIX rename cannot atomically
compare the source hash. Captures use frontmatter `kind: mind-garden-capture`, `id`,
`status: open`, and `created_at`; derived notes use `kind: mind-garden-development`
or `kind: mind-garden-distillation` and complete `derived_from` paths.

## Contextual value and same-topic routing

Persistence is an LLM judgment over the complete relevant context, not a mechanical
rule based on message type, length, a fixed list, or conversation order. Small talk,
judgments, confirmations, and corrections are frequent low-value examples, not hard
exclusions. When context continues the same topic, first merge it into the current
unsaved draft. If an explicitly identified in-scope note is clearly related, propose
a managed development append to that note. Recommend a new capture only when the
thought is both durable and independent. A bounded lexical retrieval can help find
candidates but cannot select a target or make a write.

## Managed development and connection regions

Every newly rendered capture, development, and distillation contains exactly one of
each marker pair, in this order:

```text
<!-- mind-garden:development:start -->
... managed development entries ...
<!-- mind-garden:development:end -->

<!-- mind-garden:connections:start -->
... managed path-qualified links only ...
<!-- mind-garden:connections:end -->
```

`patch_managed_development(original_text, user_contribution, agent_development,
created_at)` may append only at the tail of the development region. It renders each
user contribution unchanged inside a dynamic backtick fence longer than every
backtick run in that contribution, and labels Agent development separately. On every
repeat append, all prior bytes in both managed regions remain word-for-word unchanged;
only the development tail is added. A missing, duplicate, malformed, or misordered
marker in a legacy note fails closed: no patch implicitly upgrades the note.

`patch_managed_connections` may replace only the connections region and supports all
three note kinds. For captures it additionally verifies that the Original expression
digest is unchanged. It also fails closed unless both complete marker pairs are
already present, so it cannot silently upgrade an old capture.

## Literal capture invariant

A capture has an `## Original expression (literal; do not rewrite)` region enclosed
by a dynamic backtick fence longer than any run in the original input. The exact
input code points occur unchanged between the opening and closing fence. Pseudo
wikilinks and Markdown inside it are never interpreted, normalized, escaped, or
improved. `original_expression_digest` protects that entire original region and is
unchanged by either managed-region patch.

## Links and provenance

Every generated internal link is vault-root-relative, extensionless, and
path-qualified: `[[Mind Garden/captures/mg-123|display]]`. Link target and display
are independently validated/escaped. A derivative lists every selected source,
visible link, and SHA-256; source content is never overwritten. Missing, external,
ambiguous, bare, abbreviated, embedded, and invalid-anchor links remain literal
unresolved text.

After a substantive artifact is saved and read back, bounded lexical retrieval may
offer no more than three strong connection candidates. A single weak keyword match is
not enough. Each unsaved offer includes source, target, reason, both hashes, and the
exact unified diff for the target connection region. The connection has its own fresh
confirmation and is never auto-written as part of saving the source artifact.

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
