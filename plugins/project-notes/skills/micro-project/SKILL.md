---
name: micro-project
description: Set up and maintain a lightweight per-project wiki that tracks what is known, what is still open, and what needs doing. Use this whenever the user starts a new micro-project or one-shot, asks to initialize or scaffold a project folder, says "process the inbox", asks to log or record what was learned in a session, asks "what do we know so far" or "what's still open here", wants to add or close a local task, or is wrapping a short-lived project up. Also use it when a session in a project folder has produced findings worth keeping, even if the user has not explicitly asked for them to be written down.
---

# Micro-project

A micro-project is a short-lived piece of work — days to a few months — that
generates enough correspondence, findings and loose ends to need a memory, but
not enough to justify a full knowledge base. A dbGaP submission. A vendor
evaluation. Chasing down one recurring failure.

This skill maintains a small wiki in the project folder: what is known, what is
still open, what needs doing. It has five modes. Identify which one applies
before doing anything.

| The user says | Mode |
|---|---|
| "start a micro-project", "initialize this folder", "set this up" | **Init** |
| "log this", "write that down", "update the notes", "add a task" | **Capture** |
| "process the inbox" | **Inbox** |
| "what do we know", "what's open", "where does this stand" | **Status** |
| "we're done", "close this out", "wrap up" | **Closeout** |

Operate on the folder the session is pointed at. Do not assume a parent
directory or try to enumerate other micro-projects.

## Layout

Seed small. Five files, then grow.

```
<project>/
├── CLAUDE.md      ← thin: what this is, file map, project-specific rules
├── README.md      ← what/why/status, for a human arriving cold
├── NOTES.md       ← the wiki: what is known + open questions
├── TASKS.md       ← local task list
├── .gitignore
├── inbox/         ← staging for raw material; gitignored except README.md
└── sources/       ← created on first preserved source, not before
```

**The growth rule.** Everything starts as a section of `NOTES.md`. When a
section passes roughly 40 lines, or clearly covers a topic someone would
navigate to directly, promote it to its own file (`people.md`, `glossary.md`,
`systems/<name>.md`) and leave a one-line pointer behind in `NOTES.md`. Do not
create a file in anticipation of content. An empty scaffold trains the reader to
ignore the scaffold.

Filenames are lowercase and hyphen-separated. Dates are ISO (`2026-08-18`),
never relative.

## Voice and attribution

This is the convention that makes the wiki trustworthy six months later. Read
`references/conventions.md` before writing wiki content for the first time in a
session. The short version:

- **Established facts** are stated in third person, with a source on any claim
  that is not self-evident:
  `The study accession is phs000000. — *dbGaP confirmation email, 2026-07-30*`
- **Anything less than established** is an attributed line, prefixed with an ISO
  date and initials. First person is fine inside one:
  `2026-08-18 WH: I think they want us to give them a checklist of registration tasks.`
- **Inferences drawn by an AI session** use the `AI` initials, always:
  `2026-08-18 AI: The 2026-08-14 thread implies consent group 2 was dropped, but no message says so directly.`
- **Never** write a bare first-person sentence outside an attributed line, and
  never leave an opinion unattributed. If you cannot attribute it, it is not
  ready to write down.

## Init

1. Check what is already there. Never overwrite an existing `README.md`,
   `NOTES.md`, `TASKS.md` or `CLAUDE.md` — report what exists and scaffold only
   the gaps.
2. Copy the templates from `assets/templates/` into the folder, filling the
   placeholders. Infer the project name from the folder name; ask for the
   one-line purpose if it is not obvious from the folder's contents or the
   conversation.
3. If `inbox/` does not exist, create it with its `README.md`.
4. `git init`, then commit the scaffold as `Initialize micro-project`. No remote
   unless asked.
5. If the folder already contains raw material, say so and offer to process it —
   do not process it unprompted.

## Capture

Two triggers.

**Explicit.** The user asks for something to be written down. Write it, then
report the one-line change. No plan step, no ceremony.

**End-of-session sweep.** When a session has produced findings and the user has
not asked for them to be recorded, propose the write-up before doing it. Show a
compact plan — file, section, and the actual lines to be added — and wait for a
yes. Do not write files as a side effect of a plan the user has not seen.

Both paths follow the same placement rules:

- A durable fact about the project → the matching section of `NOTES.md`.
- Something not yet known, that someone could answer → `## Open questions` in
  `NOTES.md`, phrased as a question with the person who can answer it named
  where that is knowable.
- Something to be *done* → `TASKS.md`. A question you need to ask is a task; the
  question itself is an open question. Both entries are correct — cross-reference
  them rather than choosing.
- Raw material worth keeping → `sources/`, with a provenance line.

When an open question gets answered, move it out of `## Open questions` and into
the body as a fact with its source. Do not leave answered questions in place
with the answer appended.

## Inbox

`inbox/` is a staging area for raw material — emails, PDFs, transcripts,
screenshots, exports. Its contents are gitignored; only its `README.md` is
tracked.

**Trigger.** Only on an explicit request. Do not scan the inbox at session
start.

**Protocol.**

1. List the items, ignoring `README.md` and `.DS_Store`.
2. Read each one fully enough to know what it contains and where it should go.
3. Present **one batched plan covering every item** before making any edit. Per
   item: what facts it carries, which files will be created or changed, whether
   the source is preserved or dropped, and anything the curator needs to decide.
4. Execute after confirmation.
5. End state: `inbox/` empty except `README.md`; new content in `NOTES.md` and
   `TASKS.md`; preserved material under `sources/` with provenance.
6. Commit as one commit summarizing the batch.

**Default dispositions.**

| Source type | Default |
|---|---|
| `.eml` email | Ephemeral. Distill the facts, cite sender/date/subject in the source line, delete the original. |
| PDF, transcript, screenshot, slide deck | Preserve under `sources/` with a provenance note. |
| Spreadsheet export | Ask. |
| Anything else | Ask. |

**Sanitization.** Flag personally identifying information — home addresses,
personal phone numbers, government IDs, health information, financial details —
and ask before distilling any of it. Internal ticket numbers and work names are
fine. Never commit credentials of any kind. When in doubt, ask.

## Status

Read `README.md`, `NOTES.md` and `TASKS.md` and answer in prose, not by dumping
the files. Lead with where the project actually stands, then the open questions
that are blocking, then the open tasks. Call out anything that has gone stale —
an open question older than a few weeks with no movement is a finding in itself.

## Closeout

1. Write an `## Outcome` section at the top of `README.md`: what happened, the
   date it concluded, and the final state.
2. Resolve every open task and every open question. Each one is either closed
   with its answer or explicitly marked abandoned — nothing is left hanging.
3. Set the status line in `README.md` to `Closed <ISO date>`.
4. List the facts that deserve promotion to a durable knowledge base, and say
   why for each. **Propose only.** Do not write to another repository.
5. Commit as `Close out micro-project`.

## Git

`git init` at initialization, commit after each maintenance pass, no remote
unless asked. `inbox/` and `local/` are gitignored. Commit messages describe the
change to the project's understanding, not the file operation: `Record dbGaP
study accession and consent group decision`, not `Update NOTES.md`.

**When the folder is a mounted share** — a Cowork device-bridge mount, or any
filesystem that refuses `unlink` — git cannot remove its own lock files, so
every write leaves a stale `.git/index.lock` or `.git/HEAD.lock` that blocks the
next git command. Two consequences:

- Rename the stale locks out of the way immediately before each git write:
  `for f in .git/HEAD.lock .git/index.lock .git/objects/maintenance.lock; do
  [ -e "$f" ] && mv "$f" _to_delete/gitcruft/$(basename $f).$RANDOM; done`
  Renaming within the mount is permitted even when deleting is not.
- Run one git write per shell invocation. `git add` followed by `git commit` in
  the same breath will fail on the lock the first one left behind.

Where files cannot be deleted at all, "delete the original" becomes "move it to
`_to_delete/`" — gitignored, and left for the user to remove. Say so rather than
reporting the file as deleted.
