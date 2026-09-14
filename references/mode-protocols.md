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

## Contextual value and routing

Before selecting a mode or target, assess persistent value from the complete relevant
conversation and any explicitly selected local context. Do not mechanically decide by
message type, length, a fixed list, or chronological order. Small talk, judgments,
confirmations, and corrections are common low-value examples rather than hard
exclusions. For a same-topic continuation, merge the current unsaved draft first; if
an explicitly identified in-scope note is clearly related, propose a managed
append to it. Only a durable, independent thought warrants a new capture. A bounded
lexical scan may surface candidates but cannot choose a target or write it.

All writes, including an append or a proposed connection, require their own exact
preview and fresh confirmation.

## capture

Use capture only when the contextual routing decision is a durable, independent
thought. The create action itself does not scan or read the Vault. Render a dynamic
literal-fenced `captures/<id>.md`; the literal Original expression is unchanged and
the new capture has both empty `mind-garden:development` and
`mind-garden:connections` regions. Preview target/content without creating its
parent, confirm, then guarded exclusive-create (including the fixed `captures`
parent only if missing) and verify the exact original-region digest on read-back.

## develop

Use only explicitly selected in-scope sources. A bounded lexical scan can offer
candidates but cannot choose them. For an explicitly selected clearly related
existing capture, development, or distillation, call
`patch_managed_development(original_text, user_contribution, agent_development,
created_at)`: it dynamic-fences the unchanged user contribution, labels the Agent
development separately, and appends only at the managed-region tail while preserving
all prior managed-region text verbatim. If either marker pair is missing, duplicate,
or malformed, fail closed rather than upgrading a legacy note. Otherwise render
`developments/<id>.md` with source links, SHA-256 values, and both managed regions.
Show all inputs and the new-file or patch diff; re-read/check source hashes at
confirmation, make exactly one guarded write, then read back.

## connect

Use selected in-scope source/target and optional scoped backlink candidates only.
A target must resolve from a fully qualified scope-internal wikilink. Preview reason,
source/target hashes, and exact unified diff. `patch_managed_connections` may alter
only the connection region of a capture, development, or distillation. It requires
both complete marker pairs already exist; missing markers in old notes fail closed
without an implicit upgrade. For captures it also checks the Original expression
digest. Confirm, use `patch_expected`, and read back. Do not edit prose or infer a
link.

### Proactive proposal after save

Only after a substantive artifact has saved and passed read-back, a bounded local
lexical retrieval may offer at most three strong candidates. A weak single-keyword
match is not a proposal. Display source, target, reason, source/target hashes, and
the target connection diff for every offer. Do not write it automatically or reuse
the artifact-save confirmation: each proposed connection needs a separate fresh
confirmation and normal expected-hash patch.

## distill

Use explicitly selected sources only. Render a separate `distillations/<id>.md` with
complete provenance, visible path-qualified links, and both managed regions; never
replace or reduce a source capture. Preview the multi-source diff, confirm,
exclusive-create, and verify.

## review

Bounded-scan only scope-internal Markdown captures whose frontmatter explicitly says
`kind: mind-garden-capture` and `status: open`. Render a Markdown snapshot by
default. It is regenerable/non-authoritative, and it never changes source state or
infers urgency from mtime. An optional `.base` needs a separate user choice,
validated guarded target, exact Bases contract, preview/diff, confirmation, and
manual Obsidian render check. YAML render failure/unavailability retains the
Markdown fallback and records Base as unverified.
