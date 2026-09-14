# Mind Garden Skill

`mind-garden` is a self-contained Agent Skill for safe, literal idea capture and
deliberate development in one authorized Obsidian subdirectory.

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

## Local-only setup

Use the tracked root placeholders `config.example.json` and `config.schema.json` only
to create the machine-local configuration after a person confirms an absolute Vault
root and one non-root permitted subdirectory. The guard resolves configuration in
this order: absolute `MIND_GARDEN_CONFIG`, absolute
`$XDG_CONFIG_HOME/mind-garden/config.json`, then
`~/.config/mind-garden/config.json`. Do not create it in this repository's tests or
store a real path in docs. Validate it through `scope_guard.load_config()`; missing
configuration is a no-I/O prompt, not a default Vault choice.

## Tests

The standard-library test suite creates temporary fixture Vaults with an authorized
`Mind Garden/` directory and an unauthorized sibling. It never accesses a real
Vault or writes a local configuration. Run:

```sh
python3 scripts/scope_guard.py verify-vendor --skill-root .
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

A successful Base file test checks generated YAML/fallback semantics only. Opening
an optional Base in Obsidian is a manual, post-write compatibility check and is
non-blocking for the Markdown fallback.
