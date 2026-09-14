# Mind Garden local authorization

Mind Garden is a portable, single-root Skill. It does not discover a Vault, use the
focused Vault, or infer a directory from the active note. Its only authorization is a
machine-local configuration located outside the Skill installation.

## Configuration discovery

`scope_guard.load_config()` resolves exactly one config file in this order:

1. `MIND_GARDEN_CONFIG`, when set, must name an **absolute file path**.
2. `$XDG_CONFIG_HOME/mind-garden/config.json`, when `XDG_CONFIG_HOME` is set; the
   XDG root must be absolute.
3. `~/.config/mind-garden/config.json` when neither environment variable is set.

A missing selected file is `CONFIG_MISSING`; a relative or otherwise illegal selected
location, unreadable JSON, or invalid contract is `CONFIG_INVALID`. The guard never
falls through from an explicit or XDG selection to a different location, and never
chooses a Vault by default. It does not print configuration or Vault paths.

## First use and migration

1. Ask the user for an absolute Vault root and one non-root directory inside it.
2. Show the canonical Vault/scope and the limited operations this grants.
3. After explicit confirmation, create the selected configuration file's parent
   directory and config from the tracked root `config.example.json`; validate it
   against root `config.schema.json`. Do **not** put a real path, credential, token,
   or CLI authorization into any tracked file or the Skill installation directory.
4. On a missing, invalid, revoked, or stale configuration return a bootstrap prompt
   or unsaved draft. Do not read, scan, resolve links in, or write a Vault.

When moving machines or when the previously authorized path no longer exists, request
a fresh authorization and create or update the selected user configuration; do not
reuse or infer a replacement Vault path. The root schema and example remain tracked.

## Boundary

`scripts/scope_guard.py` is the sole product Vault-I/O boundary. It requires POSIX
descriptor-relative no-follow semantics, canonicalizes
the root and scope, rejects absolute/drive/UNC/`.`/`..`/symlink/special paths, and
re-checks containment for every read, scan, create, patch, move, review, and Base
operation. Errors use stable categories and never expose an outside path or its
content.

Retrieval is a bounded lexical scan of regular UTF-8 Markdown under the authorized
scope only. Mind Garden never runs whole-Vault `obsidian search`, `backlinks`,
`tags`, `tasks`, daily, `file=`, or default-target commands. A project-local vendor
contract may be read for compatibility instructions, but it cannot bypass this
boundary.

## Persistence

Every persistent action shows its target and preview. Existing-file changes, moves,
reviews/Bases, and multi-source derivatives additionally show a unified diff and
source SHA-256 values. A fresh explicit confirmation is required. Creates are
exclusive; edits/moves use expected source hashes and a read-back verification;
uncertain writes are never retried automatically.

To revoke access, remove or invalidate the selected user configuration. This does
not delete or modify any Vault note.

## Product limits

Mind Garden has no MCP, network client, credential store, embedding/vector recall,
database/index, background job, runtime installation, or Git automation. The
project workflow configuration disables automatic commits.
