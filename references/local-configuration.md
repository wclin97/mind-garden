# Mind Garden local configuration

Mind Garden uses one machine-local configuration outside the Skill installation. It
never guesses a Vault from the focused app or active note.

## Configuration discovery

`scope_guard.load_config()` resolves exactly one config file in this order:

1. absolute `MIND_GARDEN_CONFIG`;
2. absolute `$XDG_CONFIG_HOME/mind-garden/config.json`;
3. `~/.config/mind-garden/config.json`.

A missing file is `CONFIG_MISSING`; an illegal location, unreadable JSON, or invalid
contract is `CONFIG_INVALID`. The guard never falls through to a different location.

## First use

Ask for:

1. the absolute Obsidian Vault root that Mind Garden may read;
2. one non-root Vault-relative `allowed_subdirectory` that Mind Garden may write.

The tracked `config.example.json` and `config.schema.json` describe the v1.1 format.
The real machine-local path is not committed. A v1.0 configuration remains valid and
normalizes external enrichment to `offline`; v1.1 defaults to `automatic`.

## Read/write boundary

`scripts/scope_guard.py` is the sole Vault filesystem boundary.

- `canonical_vault` is the read root for guarded Markdown discovery.
- `canonical_scope`, derived from `allowed_subdirectory`, is the write root.
- Whole-Vault read functions never open files with write flags. A whole-Vault-only
  record outside `allowed_subdirectory` has `scope_relative_path: None` and no
  writable scope path.
- Create, patch, attachment, review-output, and Base-output APIs accept only paths
  scope-relative to `allowed_subdirectory` and remain rooted at `canonical_scope`.

Both roots are canonicalized and descriptor-walked without following symlinks.
Absolute paths, drive/UNC forms, `.`, `..`, symlinks, special files, and containment
escapes are rejected. Retrieval remains bounded by configured file, byte, and match
limits.

## Interaction and persistence

Natural-language intent inference may use guarded whole-Vault reads. It may select a
unique candidate; multiple plausible candidates or any ambiguity must be shown to the
user and require a question. Never guess.

A clear request to create a new capture or new standalone development, including its
validated attachment bundle, may write directly through the guard and read it back
without an extra preview or confirmation round. The create target remains
scope-relative to `allowed_subdirectory` and is exclusively created.

An append or patch to an existing note, every connection operation, and any overwrite
or patch of review Markdown or Base must show the target, relevant current and
proposed SHA-256 hashes, and exact unified diff and obtain fresh confirmation before
persistence. Patches require the expected source SHA-256 and successful writes are
read back and verified.

Distillation remains conservative: even after unique source discovery, show the source
list with Vault-relative paths and hashes, the scope-relative target, and exact
new-file diff, then obtain fresh confirmation before persistence. Mind Garden cannot
modify any other Obsidian folder.

## External enrichment

A v1.1 `automatic` policy may consume the documented host-provided structured
search/download capability. The Skill itself does not configure a provider. External
payloads contain no Vault paths or note content, and accepted attachments are written
only as scope-relative paths inside `allowed_subdirectory`.
