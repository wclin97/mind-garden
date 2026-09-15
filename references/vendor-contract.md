# Vendored Obsidian contract

Mind Garden depends only on the fixed project-local payload. The vendored official
contracts keep their upstream bytes but use `UPSTREAM_SKILL.md` rather than the
host-discovery filename, so the package has exactly one discoverable root entrypoint:

- `vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-markdown/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-bases/UPSTREAM_SKILL.md`

The vendor must be verified offline before Vault I/O:

```sh
python3 scripts/scope_guard.py verify-vendor --skill-root .
```

Verification requires `MANIFEST.json` schema `vendored-skill-manifest/1.0`, pinned
commit `8ccef29ae8624eccc734e77ced4a6e54baf5d83a`, MIT `LICENSE`, exactly the three
selected Skill names, the three exact `UPSTREAM_SKILL.md` contract paths with their
recorded upstream `skills/<name>/SKILL.md` source paths, disabled runtime network
fetch/no upstream Git metadata, and a SHA-256 match for every manifest file. Any mismatch returns `VENDOR_INVALID` and
only a draft/incompatibility; no global lookup, network fetch, install, or vendor
rewrite is permitted.

The local CLI contract is documentation, not authorization. Direct Obsidian CLI
retrieval is prohibited: never call `obsidian search`, `obsidian backlinks`, `obsidian tags`, `obsidian tasks`, `obsidian daily:*`, any `file=` form, or any
target-less, default, or focused-Vault command. Whole-Vault reads are allowed only
through the guarded Python scanner and link APIs. Those direct CLI forms bypass
configured-root selection, scanner caps, no-follow and UTF-8 handling, and exact path
provenance, and may default to the focused Vault or active file. The local Markdown
contract informs syntax but does not permit rewriting literal capture content. The
Bases contract applies only to optional Base output addressed by a scope-relative path
under the configured `allowed_subdirectory`; it cannot make another Vault folder
writable.
