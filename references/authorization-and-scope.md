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
- `exclusive_create`, `patch_expected`, `move_expected`, plus
  `exclusive_create_text` / `patch_expected_text` for the explicit `.base` text artifact

The guard uses canonical realpath validation before each operation plus
POSIX `O_NOFOLLOW`/`O_DIRECTORY`, descriptor-relative `lstat`/`fstat`, regular-file
checks, and read-back hash verification. A host without these trusted semantics
fails closed with `UNSUPPORTED_SAFE_IO`; it must not fall back to ordinary path I/O.

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
