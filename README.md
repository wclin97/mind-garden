# Mind Garden Skill

`mind-garden` is a self-contained Agent Skill that can discover ideas across one
configured Obsidian Vault while creating or modifying files only inside the
user-configured `allowed_subdirectory` (the configured write folder).

## Host discovery

Hosts should discover only the root `SKILL.md`: Pi recursively discovers files with
that name below `~/.agents/skills`, so the vendored official contracts intentionally
use the non-discovery filename `UPSTREAM_SKILL.md`. Mind Garden directly loads only
these fixed local payloads inside its own root:

- `vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-markdown/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-bases/UPSTREAM_SKILL.md`

If a host cannot load any exact local path, Mind Garden is incompatible for
Vault-facing work and must return a draft. It must never look up a global Skill or
fetch a runtime dependency.

## Local setup and optional external enrichment

Use the tracked root placeholders `config.example.json` and `config.schema.json` to
create the machine-local configuration. `vault_path` is the guarded Markdown read
boundary; `allowed_subdirectory` is the only write boundary. The tracked v1.1 example
defaults to `external_enrichment.mode: automatic`; its closed policy contains only
bounded search, image, byte, and excerpt limits. A v1.0 local configuration remains
valid but is normalized to offline and is never silently rewritten or granted
networking authority. Migrating it requires a separately confirmed machine-local
configuration preview. The guard resolves configuration in this order: absolute
`MIND_GARDEN_CONFIG`, absolute `$XDG_CONFIG_HOME/mind-garden/config.json`, then
`~/.config/mind-garden/config.json`. Do not create it in this repository's tests or
store a real path in docs. Validate it through `scope_guard.load_config()`; missing
configuration is a no-I/O prompt, not a default Vault choice.

## Host-provided capability boundary

Mind Garden is not a network client. During `develop` only, a v1.1 `automatic` policy
can use an already-available **structured host-provided** search/download capability.
The Skill does not name/configure a provider or implement direct HTTP, SDK, MCP,
credentials, runtime installation, or transfer tooling. It sends only a locally
derived 2–6 word query (maximum 120 characters) and a numeric result cap; no Vault
path, note content, local metadata, or long copied expression leaves the device. The
configurable search preference is 1..10, but an `ExternalSearchRequest` sends and
accepts no more than five results. Its exact two-field payload is retained locally;
any host query echo is comparison-only and can never impersonate local provenance.

Inbound titles, excerpts, URLs, and image metadata are untrusted evidence rather than
instructions. Missing, failed, empty, or unsafe host work falls back to local
development. Images are accepted only as bounded PNG/JPEG/WebP raster bytes,
content-addressed below `attachments/`, and written only inside the configured
`allowed_subdirectory`. See [external-enrichment.md](references/external-enrichment.md)
for the full protocol.

## Interaction policy

Natural-language intent inference and guarded whole-Vault reads may select one unique
candidate. Multiple plausible candidates are always shown to the user and require a
question; Mind Garden never guesses.

A clear request to create a **new capture** or **new standalone development**, including
its validated attachment bundle, may write directly through the guard and read the
artifact back without an extra preview or confirmation round. All other persistence
uses the policy in `SKILL.md`: appending to or patching an existing note, every
connection operation, and overwriting or patching review Markdown or Base must show
the target, relevant hashes, and exact diff and obtain fresh confirmation. Distillation
remains conservative: show its source list and exact diff, then obtain fresh
confirmation before persistence.

## Tests

The standard-library test suite creates temporary fixture Vaults with a configurable
`allowed_subdirectory` write folder and read-only sibling directories, plus fake
in-process recording host capabilities. It verifies that whole-Vault reads succeed
while every write remains confined to the configured `allowed_subdirectory`. It never
accesses a real Vault, real configuration, or real network, and never writes vendor.
Run:

```sh
python3 -m unittest tests.test_config_contract -v
python3 -m unittest tests.test_scope_guard -v
python3 -m unittest tests.test_artifacts tests.test_e2e -v
python3 -m unittest tests.test_skill_contract tests.test_install_copy -v
python3 scripts/scope_guard.py verify-vendor --skill-root .
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

A successful Base file test checks generated YAML/fallback semantics only. Opening
an optional Base in Obsidian is a manual, post-write compatibility check and is
non-blocking for the Markdown fallback.
