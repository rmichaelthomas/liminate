---
name: liminate-docs-propagation
description: >-
  Propagates documentation updates across the Liminate repo family after
  vocabulary additions, architectural changes, or feature releases.
  Trigger when Rob says "update all the docs," "propagate this across
  repos," "update READMEs," "sync the docs," "docs pass," or after a
  build session that changed vocabulary, verbs, connectives, or public
  API surfaces. Produces ordered update instructions per repo, a website
  handoff packet for liminate-site, and optionally a build prompt for
  Claude Code. Co-triggers liminate-session-contracts if not already
  active. Do NOT use for archival documents (checkpoints, addenda, gap
  inventories) — those are historical records and must not be modified.
---

# Liminate Docs Propagation

## What This Skill Is For

After a vocabulary addition, architectural change, or feature release lands across the Liminate ecosystem, the public-facing documentation in multiple repos needs to be updated to reflect the new state. This skill coordinates that update — identifying which documents in which repos need changes, producing the updates in dependency order, and generating a website handoff packet for liminate-site.

This is a propagation skill, not a creation skill. It does not produce new architecture or lock new decisions. It takes already-locked decisions from checkpoints and addenda and pushes them into the documentation surfaces where users, agents, and contributors will encounter them.

---

## Dual-Environment Skill

This skill is designed to work in two environments:

**Claude.ai** — Installed as a user skill. Triggered by the description keywords above. Produces update plans, website handoff packets, and optionally build prompts for Claude Code to execute.

**Claude Code CLI** — Lives in the `liminate` core repo at `docs/skills/docs-propagation.md`. Referenced from `CLAUDE.md`. When working in the `liminate` repo and asked to propagate docs, Claude Code reads this file and executes the updates directly across locally-cloned repos.

The protocol is identical in both environments. The difference is output mode: Claude.ai produces documents and build prompts; Claude Code executes the changes directly.

**Claude Code prerequisites:** All affected repos must be cloned locally. Claude Code works in the `liminate` repo as home base and `cd`s into sibling repos to make changes. Expected local layout:

```
~/projects/  (or wherever repos are cloned)
├── liminate/
├── liminate-session-contracts/
├── liminate-receipts/
├── liminate-contract-inheritance/
├── liminate-site/
├── prosecode-prompt-compiler/
├── prosecode-context-pager/
└── prosecode-handoff-packet/
```

If a repo is not cloned locally, skip it and flag it in the output. Do not fail the entire propagation because one satellite repo is missing.

---

## Session Contract Co-Trigger

When this skill activates, check whether a `liminate-session-contracts` contract is already running. If not, start one. Documentation propagation involves claims about what the current locked state IS — those claims need verification backing. Follow the two-channel protocol from `liminate-session-contracts`.

---

## Archival Exclusion Rule

**This skill NEVER modifies checkpoint documents, addenda, gap inventories, resonance signals, binders, or any document produced by `rmt-working-documents`.** Those are the historical record. When a vocabulary grows from 34 to 45 words, the inception checkpoint that says "34 reserved words" is not wrong — it was correct at the time it was locked. The propagation targets are living documents: READMEs, SKILL files, spec docs, website pages, and agent instruction files.

---

## Repo Family Map

The Liminate ecosystem spans these repos. Each has different documentation surfaces:

| Repo | Documentation surfaces | Update triggers |
|---|---|---|
| `liminate` (core) | `README.md`, `CLAUDE.md`, `AGENTS.md`, `docs/language/syntax.md`, `docs/language/quickstart.md`, `docs/spec/inscript_v1_thirty_sentences.md`, `docs/guide/reactive_patterns.md`, `docs/architecture/pipeline.md`, `docs/roadmap/v1-v2-boundary.md`, `docs/DEV_README.md` | Vocabulary changes, verb additions, connective additions, parser changes, runtime changes, new features |
| `liminate-session-contracts` | `README.md`, `SKILL.md` | New verbs/connectives that affect contract syntax, new pack definitions |
| `liminate-receipts` | `README.md` | Changes to contract storage, API, or UI |
| `liminate-contract-inheritance` | `README.md`, `SKILL.md`, `AGENTS.md` | Inheritance model changes, new verbs that affect inheritance semantics |
| `liminate-site` | `index.html`, `language/` pages, `spec/`, `learn/`, `philosophy/`, `skills/`, `start/`, `install/` | Any public-facing change — vocabulary, features, positioning |
| `prosecode-prompt-compiler` | `README.md`, `SKILL.md` | Changes to intent vocabulary, new intent verbs |
| `prosecode-context-pager` | `README.md`, `SKILL.md`, `CLAUDE.md` | Changes to paging strategy, scoring, or integration |
| `prosecode-handoff-packet` | `README.md`, `SKILL.md` | Changes to handoff structure, new sections |

---

## Pre-Propagation Protocol

Before producing any updates:

### Step 1: Identify the source of truth

What checkpoint, addendum, or build session contains the locked decisions being propagated? Confirm it is in context. The propagation must be traceable to a locked decision — do not propagate from memory or inference.

### Step 2: Identify what changed

Categorize the change:

| Change type | Affects |
|---|---|
| **Vocabulary addition** (new verb) | Core syntax docs, quickstart, spec, SKILL files that reference verb counts, website vocabulary page, README examples |
| **Vocabulary addition** (new connective) | Core syntax docs, spec, website language pages |
| **Architectural change** (parser, runtime, pipeline) | Architecture docs, DEV_README, CLAUDE.md, AGENTS.md |
| **Feature release** (new capability) | README, quickstart, website learn/start pages |
| **Pack addition** (new domain pack) | Session contracts README/SKILL (if pack affects contracts), website skills page |
| **Positioning change** (tagline, framing) | README, website index, philosophy page |

### Step 3: Scan each repo for stale references

For each affected repo, use `github_get_file` to read the documents that need updating. Search for the specific strings that will be stale — word counts, verb lists, feature descriptions. Do not assume you know what the documents say. Read them.

### Step 4: Produce the update plan

List every file that needs changing, what specifically needs to change in each, and in what order. The order matters — core repo first, then satellite repos, then website last (because the website references the other repos' READMEs and docs).

---

## Propagation Order

Updates must follow this dependency order:

1. **`liminate` (core)** — The source of truth for vocabulary, syntax, and architecture. Update here first. All other repos reference this one.
   - `docs/language/syntax.md` — vocabulary table, verb list, connective list
   - `docs/language/quickstart.md` — examples using new vocabulary
   - `docs/spec/inscript_v1_thirty_sentences.md` — spec document if word count or grammar changed
   - `README.md` — feature summary, word count, examples
   - `CLAUDE.md` / `AGENTS.md` — agent instruction files referencing vocabulary

2. **Satellite repos** (`liminate-session-contracts`, `liminate-receipts`, `liminate-contract-inheritance`, Prosecode repos) — Update only the docs that reference the changed elements. Most vocabulary additions won't touch most satellite repos.

3. **`liminate-site`** — Updated last. The website is the public face; it should reflect the final state after all repo docs are updated.

---

## Website Handoff Packet

After producing updates for all repos, generate a separate handoff packet specifically for liminate-site updates. This packet is tuned for the agent doing the website work — it needs to know what content changed, where it appears on the site, and what pages need updating.

**Filename:** `liminate_site_handoff_{YYYY_MM_DD}_{subtitle}.md`

**Structure:**

```markdown
# Liminate Site Update — Handoff Packet

**Date:** {date}
**Source:** {checkpoint/addendum that locked the changes}
**Scope:** {what changed — e.g., "vocabulary expanded from 34 to 45 words, 5 new verbs, 4 new connectives"}

## Pages Requiring Updates

| Page | Path | What to change |
|---|---|---|
| {page name} | {path in repo} | {specific change} |

## Content Diffs

For each page, the specific text that needs to change:

### {page path}

**Current text:** {exact current text from the file}
**Updated text:** {new text reflecting the locked changes}

## New Pages (if any)

| Page | Path | Content source |
|---|---|---|
| {page name} | {path} | {which checkpoint/doc provides the content} |

## Style and Tone Notes

The liminate-site uses {describe the site's current voice and style}.
All new content should match this voice. Do not introduce marketing
language, hype, or claims not backed by the locked checkpoint.

## Do Not Change

- {list any pages or sections that must NOT be modified}
- Archival content, historical references, or philosophical framing
  that is correct as-is regardless of vocabulary count
```

---

## Output Modes

The output mode depends on the environment:

**In Claude.ai** — After completing the propagation plan, offer Rob two options:

**Option A: Build prompt for Claude Code.** Produce a single build prompt (using `rmt-build-prompt` conventions) that Claude Code can execute across all affected repos. Each repo gets its own phase. Branch convention: `docs/propagate-{change-slug}` per repo.

**Option B: Manual update list.** Produce the diffs as a readable document that Rob can apply manually or hand off piecemeal.

**In Claude Code CLI** — Execute the updates directly:

1. Confirm the propagation plan with Rob before making changes.
2. For each repo in propagation order:
   - `cd` into the repo directory
   - Create a branch: `git checkout -b docs/propagate-{change-slug}`
   - Make the changes
   - `git add` and `git commit` with message: `docs: propagate {change description}`
   - Return to the `liminate` repo before moving to the next
3. After all repos are updated, produce the website handoff packet as a file in the `liminate` repo at `docs/handoffs/liminate_site_handoff_{YYYY_MM_DD}_{subtitle}.md`
4. Report: which repos were updated, which were skipped (not cloned locally), and present the website handoff packet.

Do NOT push branches or create PRs automatically. Rob pushes and PRs on his own schedule.

In all modes, the website handoff packet is always produced separately — it's a distinct deliverable because the website update may happen at a different time or by a different agent than the repo doc updates.

---

## Known Failure Modes

| # | Mode | Prevention |
|---|---|---|
| 1 | Propagating from memory instead of locked source | Step 1 requires the checkpoint to be in context. No checkpoint, no propagation. |
| 2 | Updating archival documents | Archival Exclusion Rule is explicit. Checkpoints are never modified. |
| 3 | Stale word counts in satellite repos | Step 3 requires reading each file before proposing changes. Do not assume the current count. |
| 4 | Website updated before repos | Propagation order is locked: core → satellites → website. |
| 5 | Over-propagating — changing docs that don't reference the changed element | Step 3 scans for specific stale strings. If a doc doesn't mention the changed element, it doesn't get updated. |

---

## Provenance

*Pattern derived from direct observation of: the Liminate repo family structure (8 repos scanned May 18, 2026), vocabulary expansion from 34 to 45 words (in progress, May 2026), documentation surfaces across all repos verified via `github_list_files`. The propagation order (core → satellites → website) reflects the actual dependency chain: satellite READMEs reference core docs, and the website references both.*
