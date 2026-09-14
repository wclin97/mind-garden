# Mode protocols

Each mode loads the exact local vendor contracts, verifies the offline manifest,
loads the local scope through the guard, computes an unsaved draft, previews it, and
obtains a fresh confirmation. Preview target resolution never creates directories.
After confirmation, the same exclusive create call may initialize only its missing
direct fixed artifact parent (`captures`, `developments`, `distillations`, or
`review`); reads and patches never initialize directories. Creation requires
component-wide `O_NOFOLLOW_ANY` and has no weaker fallback. `move_expected` always
fails closed because POSIX rename cannot atomically enforce an expected source hash.
Configuration/vendor/scope/confirmation failure, stale sources, invalid targets, and
unsupported capabilities produce a non-leaking unsaved draft and no retry.

## capture

Input is the user's exact expression. Do not scan or read the Vault. Render a dynamic
literal-fenced `captures/<id>.md`, preview target/content without creating its parent,
confirm, then guarded exclusive-create (including the fixed `captures` parent only if
missing) and verify the exact original-region digest on read-back.

## develop

Use only explicitly selected in-scope sources. A bounded lexical scan can offer
candidates but cannot choose them. Render `developments/<id>.md` with source links
and SHA-256 values. Show all inputs and new-file diff; re-read/check source hashes
at confirmation, exclusive-create once, then read back.

## connect

Use selected in-scope source/target and optional scoped backlink candidates only.
A target must resolve from a fully qualified scope-internal wikilink. Preview reason,
source/target hashes, and exact unified diff. Patch only connection markers through
`patch_managed_connections` and `patch_expected`; check Original expression digest
and read-back hash. Do not edit prose or infer a link.

## distill

Use explicitly selected sources only. Render a separate `distillations/<id>.md`
with complete provenance and visible path-qualified links. Preview multi-source
hashes/diff, confirm, exclusive-create, and verify. Never reduce, delete, or revise
a source capture.

## review

Bounded-scan only scope-internal Markdown captures whose frontmatter explicitly says
`kind: mind-garden-capture` and `status: open`. Render a Markdown snapshot by
default. It is regenerable/non-authoritative, and it never changes source state or
infers urgency from mtime. An optional `.base` needs a separate user choice,
validated guarded target, exact Bases contract, preview/diff, confirmation, and
manual Obsidian render check. YAML render failure/unavailability retains the
Markdown fallback and records Base as unverified.
