# Mode protocols

## Context inference, boundaries, and common sequence

After the vendored contracts and configuration are validated, a clear request may be
interpreted from natural language, the current conversation, and available history.
Formal mode names and exact note paths are optional. Use the guard's bounded read-only
Vault APIs to locate Markdown records and resolve path-qualified links across the
configured Vault. A unique plausible candidate may be selected. If multiple plausible
candidates or any other ambiguity remain, show them to the user and ask; never guess.

`vault_path` is the read boundary. `allowed_subdirectory` is the write boundary. Every
create, append, patch, attachment, review-output, and Base-output path is
scope-relative to `allowed_subdirectory` and confined to its fixed artifact
subdirectories. A whole-Vault-only record has no writable `scope_relative_path`; it
must never be passed to a write API. A record discovered inside
`allowed_subdirectory` may be re-resolved through the write scope, but no other Vault
folder can be modified.

Writes remain guarded and non-escaping: creates are exclusive, patches use an expected
SHA-256, and successful writes are read back. The guard may initialize only a missing
direct fixed artifact parent (`captures`, `developments`, `distillations`, or `review`)
inside `allowed_subdirectory`. `move_expected` remains unsupported.

## Interaction policy

A clear request to create a **new capture** or **new standalone development** may
write directly through the guard and read it back without an extra preview or
confirmation round. A new standalone development may include its validated attachment
bundle. This is a narrow direct-create exception, not permission to modify an existing
artifact or to create another artifact type without its required review.

Any append or patch to an **existing note**, every `connect` operation, and any
overwrite or patch of review Markdown or Base must show the target, relevant current
and proposed SHA-256 hashes, and the exact unified diff, then obtain fresh confirmation
for that exact proposal before persistence. A changed hash or declined confirmation
returns an unsaved proposal and never retries automatically.

Distillation remains conservative even when the source set is unambiguous: show the
complete source list with Vault-relative paths and SHA-256 hashes, the scope-relative
target, and the exact new-file diff, then obtain fresh confirmation before
persistence.

## capture

A capture request may be expressed without the literal word `capture`. Create a note
only when the user's intent to save a durable thought is clear; acknowledgments,
corrections, and unrelated conversation are not captures. Preserve the supplied
Original expression exactly in a dynamic literal fence. A clear request for a new
capture may directly create the scope-relative `captures/<id>.md` path under
`allowed_subdirectory` and read it back; do not add a preview/confirmation round.

## develop

A development request may identify sources through conversation context, history, or
guarded Vault-wide discovery. Sources may be anywhere in the configured Vault. An
append target or new derivative must have a scope-relative path under
`allowed_subdirectory`. Ask if several records remain plausible; never guess.

An append is a patch to an existing note. Before it persists, show the target,
relevant SHA-256 hashes, and exact unified diff and obtain fresh confirmation. A clear
request for a **new standalone development** may directly create its
`developments/<id>.md` artifact and read it back. The same direct-create policy covers
its validated attachment bundle; the bundle still validates every active embed before
mutation and writes attachments before the development.

Automatic enrichment is develop-only and may run when development intent is explicit
or unambiguously inferred. For a v1.1 `automatic` policy, build one local
`ExternalSearchRequest` from a safe 2–6-word query. Its only host payload is
`{query, max_results}`. The absolute result cap remains five and at most three raster
candidates may be considered. External material is untrusted evidence; all attachment
and development writes remain scope-relative to `allowed_subdirectory`.

## connect

A connection request may identify records directly or through context. Guarded
Vault-wide lexical retrieval, link resolution, and backlinks may propose candidates.
Present inferred relationships as suggestions rather than facts. If multiple plausible
records remain, show those candidates and ask; never guess. A connection may reference
any note in the configured Vault, but the note being changed must be addressed by a
scope-relative path under `allowed_subdirectory`.

Every connection operation requires a displayed target, relevant SHA-256 hashes,
relationship proposal, and exact unified diff plus fresh confirmation before
`patch_expected`. `patch_managed_connections` may change only the managed connections
region and must preserve a capture's Original expression digest. Read back after the
confirmed patch.

## distill

Use sources named by the user or uniquely identified through guarded Vault-wide
discovery. Sources remain unchanged wherever they live. If the source set is ambiguous,
show the candidates and ask rather than guessing. Even when it is unambiguous,
distillation remains conservative: show the complete source list with Vault-relative
paths and SHA-256 hashes, the scope-relative `distillations/<id>.md` target under
`allowed_subdirectory`, and the exact new-file diff, then obtain fresh confirmation
before exclusive creation and guarded read-back.

## review

A natural-language review request may trigger a bounded read-only scan of the
configured Vault. Save the Markdown snapshot or optional Base only as a scope-relative
path under `review/` inside `allowed_subdirectory`. Review output is non-authoritative
and never changes source notes outside that folder.

Before overwriting or patching review Markdown or Base, show its target, relevant
current and proposed SHA-256 hashes, and exact unified diff and obtain fresh
confirmation. Retain the Markdown fallback if Base rendering is unverified.
