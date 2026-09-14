---
name: mind-garden
description: Safely capture, develop, connect, distill, and review fragmentary ideas in one explicitly authorized Obsidian subdirectory. Use only after following the local authorization and scope guard protocol.
---

# Mind Garden

Mind Garden preserves authorship: it captures original thoughts literally, proposes
connections rather than inventing them, and makes every persistent change explicit.
It assesses whether an artifact deserves persistence from the complete relevant
conversation and selected local context, not from a mechanical message classifier.
It is a self-contained Skill at the repository root; the root `SKILL.md` is the only
discoverable entrypoint, including for hosts that recursively discover `SKILL.md`
below an install directory. No global Skill with a similar name is a fallback.

## Non-negotiable loading and safety gate

Before a mode can access a Vault:

1. Load these **exact Skill-relative vendored official contracts** directly (and no
global copy). They deliberately use the non-discovery filename
`UPSTREAM_SKILL.md` so this package exposes only its root entrypoint:
   - `vendor/kepano-obsidian-skills/skills/obsidian-cli/UPSTREAM_SKILL.md`
   - `vendor/kepano-obsidian-skills/skills/obsidian-markdown/UPSTREAM_SKILL.md`
   - `vendor/kepano-obsidian-skills/skills/obsidian-bases/UPSTREAM_SKILL.md` (review Base only)
2. Verify the vendored contracts before any Vault I/O from the Skill root:
   `python3 scripts/scope_guard.py verify-vendor --skill-root .`
   A missing, mismatched, or host-unloadable local vendor produces an incompatibility
   or unsaved draft. Never download, install, update, or globally search for a Skill.
3. Read [authorization-and-scope.md](references/authorization-and-scope.md). Load
   configuration only through `scope_guard.load_config()`. If it is absent or
   invalid, request explicit authorization and return an unsaved draft; do not select,
   enumerate, read, or write a default/focused Vault.
4. Use `scope_guard.py` for **all** Vault-facing reads, scans, link resolution,
   creates, patches, moves, fixed artifact-parent initialization, Markdown review
   snapshots, and optional Base targets. It is the only product filesystem boundary.
   Do not substitute shell, editor, Python snippets, or Obsidian CLI operations.
5. Read [artifact-schema.md](references/artifact-schema.md) and the relevant mode
   in [mode-protocols.md](references/mode-protocols.md). Only bounded local lexical
   retrieval and scoped backlink parsing are permitted. Never issue `obsidian search`,
   `obsidian backlinks`, `obsidian tags`, `obsidian tasks`, `obsidian daily:*`, `file=`,
   or a target-less/default Vault CLI.

The guard rejects absolute targets, Windows drive/UNC/device forms, empty paths,
`.`/`..`, symlinks, special files, and containment changes detected during guarded
path resolution. Creation requires component-wide `O_NOFOLLOW_ANY` support and
resolves the final fixed artifact path from a fresh scope-root descriptor; there is
no weaker fallback. During any operation, an uncooperative same-user process must
not concurrently rename or replace the configured scope, its ancestors, any directory
inside the authorized scope tree (including artifact parents), or the target leaf;
public POSIX APIs cannot enforce that hostile namespace boundary. Do not disclose an
external pathname or content in a response. Generated references must be unique,
Vault-root-relative, extensionless, path-qualified wikilinks such as
`[[Mind Garden/captures/mg-example|an idea]]`; bare titles, aliases, URLs, embeds,
ambiguous names, external paths, and invalid anchors remain unresolved text.

## Common persistent-action sequence

1. Receive a specific user intent. Never infer authorization or a target.
2. Validate vendor and local configuration; identify selected in-scope sources via
   `scan_markdown`, `read_markdown`, `resolve_wikilink`, or `backlinks` only.
3. Display selected scope (without outside paths), target, bounded limits, source
   paths/hashes, and an unsaved proposed artifact.
4. Display a preview for every write. For edits, reviews/Bases, and multi-source
   derivatives also display a unified diff and all source hashes.
5. Collect a fresh, unambiguous confirmation for this exact preview. Decline,
   missing confirmation, stale source, invalid target, unavailable capability, or
   vendor/config failure returns only the draft; do not write or auto-retry.
6. Make exactly one guarded `exclusive_create`, `patch_expected`,
   `exclusive_create_text`, or `patch_expected_text` call. As part of that same
   confirmed create, the guard may descriptor-relatively create only a missing direct
   parent named `captures`, `developments`, `distillations`, or `review`; preview
   resolution never creates it, and reads/patches never initialize directories.
   Creation fails closed with `UNSUPPORTED_SAFE_IO` when component-wide
   `O_NOFOLLOW_ANY` is unavailable. `move_expected` remains a compatibility API but
   always fails closed with `UNSUPPORTED_SAFE_IO` because POSIX rename has no atomic
   expected-hash precondition. The text variants exist only for a reviewed optional
   `.base`. Read back with the guard and verify the expected hash/structure before
   reporting the saved in-scope location.

## Contextual value and note routing

Before proposing a persistent artifact, the LLM considers the complete relevant
conversation, the user's purpose, corrections, and any explicitly selected local
context. It must not decide by message type, length, a fixed checklist, or message
order. Small talk, a judgment, a confirmation, or a correction are common examples
of low persistent value, but none is a hard exclusion: any can contain a durable
insight in context.

When a substantive thought is about the same topic, first merge it into the current
unsaved draft. If an explicitly identified existing in-scope note is clearly about
the same topic, propose an append to that note's managed development region instead
of creating a duplicate; show the existing target and exact append, then require the
normal fresh confirmation. Recommend a new capture only for a durable, independent
thought. A bounded lexical scan can surface candidates, but it never selects or
writes a target on its own, and a merely weak keyword overlap is not sufficient to
call notes related.

## Modes

### capture

Use this create operation only after contextual routing identifies a durable,
independent thought. The create itself does not scan or read Vault content. Create a
draft `captures/<id>.md` whose **Original expression** is a dynamic fenced literal
region containing the user's supplied text unchanged (including CJK, emoji,
Markdown, fence runs, and leading/trailing whitespace). A new capture also contains
empty `mind-garden:development` and `mind-garden:connections` managed regions.
Preview the exact target/content without creating directories; on confirmation call
`exclusive_create`, which may initialize only the missing direct `captures` parent
as part of that same guarded operation. Read back and compare the original-region
digest. Never rewrite or "improve" the original thought.

### develop

Use only sources the user explicitly selects from permitted scan results. For a
clearly same-topic existing note selected by the user, use
`patch_managed_development` to append a dynamic-fenced literal **User contribution**
and separately labelled **Agent development**; it preserves every existing managed
region byte-for-byte and appends only at its tail. Missing or malformed markers in a
legacy note fail closed rather than upgrading it. Otherwise build a new
`developments/<id>.md` with visible, path-qualified source links and each source
SHA-256 provenance. New development notes contain both managed regions. Preview all
source hashes and the exact new-file or patch diff, then obtain fresh confirmation
and make one guarded write. If a source changes before writing, return an unsaved
draft.

### connect

Read only user-selected in-scope source/target and optional scoped backlink candidates.
A target must resolve from a fully qualified scope-internal wikilink. Preview reason,
source/target hashes, and exact unified diff. `patch_managed_connections` may change
only the `mind-garden:connections` region of a capture, development, or distillation;
for a capture it also proves the Original expression digest is unchanged. Both
managed-region marker pairs must already be present exactly once: a legacy note with
a missing marker fails closed and is never implicitly upgraded. Confirm, use
`patch_expected`, and read back. Never infer a connection or rewrite source text.

### proactive connection proposals

After a substantive artifact has been saved and verified, the Skill may run only a
bounded in-scope lexical retrieval and offer at most three strong candidates. A
candidate needs multiple specific lexical signals; a weak single-keyword match is not
proposed. Each offer displays source, target, reason, both hashes, and the exact
connection-region unified diff. It remains an unsaved proposal until the user gives a
separate fresh confirmation for that exact connection preview; retrieval and saving
the source never auto-create a connection.

### distill

Use only explicitly selected sources. Create a separate `distillations/<id>.md` with
complete provenance, visible path-qualified links, and both
`mind-garden:development` and `mind-garden:connections` managed regions; never
replace or compress the sources. Preview the multi-source diff, confirm, then
exclusive-create and verify.

### review

Scan only the authorized scope and only capture notes with explicit
`kind: mind-garden-capture` and `status: open` metadata. The default is a
regenerable Markdown snapshot at `review/Mind Garden Review.md`; it is
non-authoritative and does not change capture state or infer urgency from mtime.
Preview/diff/confirm, then guarded-create or expected-hash patch. A `.base` is
strictly opt-in after loading the exact local Bases contract, validating a guarded
target, and confirming a folder/kind/status/`.md` filter. Save it only with
`exclusive_create_text` or `patch_expected_text`, then perform the manual render
check. If Base generation or Obsidian rendering cannot be verified, retain the
Markdown fallback and report it as unverified; do not change captures.

## Prohibited capabilities

Do not add or use MCP, network/HTTP, embedding/vector recall, database/index,
credentials, background jobs, runtime dependency installation, global Skills,
whole-Vault queries, automatic Git actions, batch edits, deletion, or real-Vault
access during implementation/testing. Use disposable fixture Vaults only for tests.
