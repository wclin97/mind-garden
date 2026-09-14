# Vendored upstream: kepano/obsidian-skills

- **Source:** https://github.com/kepano/obsidian-skills.git
- **Pinned commit:** `8ccef29ae8624eccc734e77ced4a6e54baf5d83a`
- **License:** MIT; the unmodified upstream license is retained as `LICENSE`.
- **Purpose:** portable, project-local dependencies for the future Mind Garden Agent Skill.

## Selected upstream skills

Only the currently required skills are included:

- `skills/obsidian-cli/`
- `skills/obsidian-markdown/`
- `skills/obsidian-bases/`

`json-canvas`, `knap`, and all other upstream skills are deliberately excluded: no current Mind Garden requirement needs them. Add one only after an explicit requirement and license/provenance review.

## Loading contract

The future Mind Garden skill must load and delegate to these exact project-local
paths rather than rely on a user-global installation or runtime download. The files
retain the byte-identical upstream contract content, but use `UPSTREAM_SKILL.md` so
recursive host discovery exposes only Mind Garden's root `SKILL.md`:

- `vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-markdown/UPSTREAM_SKILL.md`
- `vendor/kepano-obsidian-skills/skills/obsidian-bases/UPSTREAM_SKILL.md`

`MANIFEST.json` records each renamed contract's upstream source path as
`skills/<name>/SKILL.md`, its installed path as
`skills/<name>/UPSTREAM_SKILL.md`, and the unchanged upstream SHA-256.

The target host's project-local skill-discovery/delegation behavior remains a compatibility check. This vendor directory is source material, not permission to access an Obsidian Vault. Any future `obsidian-cli` operation remains explicitly user-authorized and must observe Mind Garden's no-direct-Vault-access policy.

## Update procedure

1. Obtain a disposable verified upstream checkout outside this project; do not clone or retain upstream `.git` metadata here.
2. Verify the desired upstream commit and license; inspect the diff for only the selected skill trees.
3. Copy each selected upstream `skills/<name>/SKILL.md` byte-for-byte to its local
   `skills/<name>/UPSTREAM_SKILL.md`; retain reference filenames unchanged. Update
   `MANIFEST.json`, including both paths and unchanged SHA-256 values, this file's
   pin, and provenance values together.
4. Review changes and project compatibility before committing in a future, separately authorized change. This initialization does not make a Git commit and never performs a runtime network fetch.
