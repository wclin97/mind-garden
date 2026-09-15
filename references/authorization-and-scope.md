# Authorization and read/write boundaries

## Authorization state

The machine-local configuration selects one Obsidian `vault_path` and one
`allowed_subdirectory` inside it. The Vault root is the guarded read boundary.
`allowed_subdirectory` is the only write boundary. Existing v1.0 and v1.1
configurations use this meaning without migration.

The resolution order is an absolute `MIND_GARDEN_CONFIG` file, an absolute
`$XDG_CONFIG_HOME/mind-garden/config.json`, then
`~/.config/mind-garden/config.json`. A relative override or XDG root is invalid. When
the config is absent or invalid, return `CONFIG_MISSING` or `CONFIG_INVALID` and ask
for configuration rather than choosing a focused/default Vault.

## Guard API

All Vault filesystem I/O passes through `scripts/scope_guard.py`.

Whole-Vault read-only APIs:

- `resolve_vault_target(ctx, vault_relative_path)` resolves only an existing regular
  `.md` file; directory, symlink, special-file, and non-Markdown targets are rejected
- `read_vault_markdown(ctx, vault_relative_path)`
- `scan_vault_markdown(ctx, query, max_files, max_bytes, max_matches)`
- `resolve_vault_wikilink(ctx, source, raw, known_notes)`
- `backlinks_vault(ctx, target_vault_relative_path, known_notes)`

A whole-Vault record outside `allowed_subdirectory` has `scope_relative_path: None`.
It has no writable scope path; its `vault_relative_path` remains available only for
provenance and links. A record discovered by a whole-Vault read is never a write target
until it is re-resolved as a scope-relative target under `allowed_subdirectory`.

Write-scope and compatibility APIs:

- `resolve_target`, `read_markdown`, `scan_markdown`, `resolve_wikilink`, and
  `backlinks` retain their scope-relative behavior
- `scope_path_for_write(ctx, record)` is the narrow existing-record bridge to a
  write-scope path; it rejects a `None` path before a write API is called
- `exclusive_create`, `patch_expected`, `exclusive_create_text`, and
  `patch_expected_text` accept only paths scope-relative to `allowed_subdirectory`
- `rename_content_note_expected` is the only supported rename: it accepts only an
  expected-hash guarded migration of a regular Markdown legacy content note within
  one direct `captures`, `developments`, or `distillations` directory to a canonical
  readable filename; it is descriptor-relative under `canonical_scope` and assumes a
  single namespace owner during the final no-replace checks
- `plan_raster_attachment`, `read_attachment`, and
  `exclusive_create_development_bundle` keep attachment paths scope-relative to
  `allowed_subdirectory`
- `move_expected` remains unsupported

Conversation, history, host results, and model judgment may guide whole-Vault reads,
but no input can move a write API's descriptor root outside `canonical_scope`, derived
from `allowed_subdirectory`.

## Path behavior

Read APIs start from a fresh canonical Vault descriptor. Write APIs start from a fresh
canonical write-scope descriptor. Both reject absolute paths, drive/UNC/device forms,
backslashes, NUL/control characters, empty components, `.`, `..`, symlinks, and
special files. Reads cannot escape the Vault; all writes are scope-relative to
`allowed_subdirectory` and cannot escape it.

The scanner reads only regular UTF-8 Markdown and obeys configured file, byte, and
match caps. It does not follow symlinks. Generated wikilinks are unique,
Vault-root-relative, extensionless, and path-qualified. Bare, ambiguous, URL, embedded,
malformed, outside-Vault, and invalid-anchor targets remain unresolved.

Direct Obsidian CLI retrieval is prohibited: never call `obsidian search`, `obsidian backlinks`, `obsidian tags`, `obsidian tasks`, `obsidian daily:*`, any `file=` form, or
any target-less, default, or focused-Vault command. Whole-Vault reads are allowed, but
only through these guarded Python APIs. The direct CLI forms bypass configured-root
selection, scanner caps, no-follow and UTF-8 handling, and exact path provenance, and
may default to the focused Vault or active file.

## Interaction and persistence

Natural-language intent inference may guide guarded discovery. A unique plausible
candidate may be selected; multiple plausible candidates or other ambiguity must be
shown to the user and require a question. Never guess.

A clear request for a new capture or new standalone development, including its
validated attachment bundle, may write directly through the guard and read it back
without an extra preview or confirmation round. The guard still enforces exclusive
creation, validation, and read-back verification.

Any append or patch to an existing note, every connection operation, and every
overwrite or patch of review Markdown or Base must show the scope-relative target,
relevant current and proposed SHA-256 hashes, and the exact unified diff, then obtain
fresh confirmation before persistence. Existing-note edits retain expected SHA-256
preconditions; successful writes are immediately guarded-read and verified.

A legacy content-note rename is permitted only after an explicit user request plus a
complete from/to/hash/content-diff preview and fresh confirmation. The preview names
both scope-relative paths, presents the current expected SHA-256, and shows the exact
unchanged content diff. `rename_content_note_expected` only performs a same-directory
content-note migration under the configured write scope; generic move remains
unsupported. It preserves the stable frontmatter ID. If the guarded destination
read-back or source-absence check leaves a partial migration, stop without automatic
retry or rollback.

Distillation remains conservative: even when its sources were uniquely identified,
show the source list with Vault-relative paths and hashes, the scope-relative target,
and the exact new-file diff, then obtain fresh confirmation before persistence. Other
Vault folders are always read-only to Mind Garden.

## External boundary

External search receives only a locally derived bounded query and result cap. No Vault
path, filename, note ID, frontmatter, source hash, wikilink, Markdown, Original
expression, or copied note fragment crosses that boundary. Incoming evidence and
raster bytes remain untrusted. Any accepted attachment is content-addressed and saved
only as a scope-relative path inside `allowed_subdirectory`.
