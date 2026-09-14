# Conventions

Read this before writing wiki content for the first time in a session.

## Why attribution, and not just prose

A micro-project wiki is written by at least two authors — the curator and
whatever AI session is running — and read months later by someone who has
forgotten which was which. Unattributed prose loses that distinction
permanently. "The consent groups were merged at the sponsor's request" reads as
established fact whether it came from a signed email or a model's guess three
minutes after skimming one thread.

So: every claim in the wiki is either established and sourced, or attributed to
a person on a dated line. There is no third category.

## The two forms

**Established fact.** Third person, no hedging, source appended when the claim
is not self-evident:

```markdown
The study accession is phs000000.v1.p1. — *dbGaP confirmation, 2026-07-30*

Submission requires an approved DUC before subject data can be uploaded.
```

The second line needs no source — it is general dbGaP behaviour, not a fact
about this project. Source lines are for things a reader might reasonably
challenge.

**Attributed line.** ISO date, initials, colon. First person is fine and
expected inside one:

```markdown
2026-08-18 WH: I think they want us to give them a checklist of registration
tasks rather than a narrative status update.

2026-08-18 AI: The 2026-08-14 thread implies consent group 2 was dropped, but
no message states it directly.
```

Initials are the person's, uppercase. AI sessions use `AI` — never the
curator's initials, never a bare unattributed line, no exceptions. If a session
writes down its own inference as though it were the curator's judgment, the
whole convention is worthless.

## Promotion

An attributed line is a candidate, not a conclusion. When it gets confirmed,
rewrite it as an established fact with the confirming source and delete the
attributed line. Do not stack a confirmation underneath a guess — the wiki
should read as what is currently believed, not as a transcript of how belief
arrived.

At closeout, this distinction does the sorting for you: established facts with
document sources are promotable to a durable KB as-is; attributed lines either
got confirmed along the way or they die with the project.

## What never goes in

- Credentials of any kind — passwords, tokens, keys, certificate contents.
- Unsanitized personally identifying information: home addresses, personal
  phone numbers, government IDs, health information, financial details.
- Candid personal assessments of named colleagues. Working notes about a
  project are not the place; if it matters, it belongs somewhere private.
- Speculation about other organizations' motives stated as fact. Speculation is
  fine — on an attributed line, marked as such.

## Style

- ISO dates everywhere. `2026-08-18`, never "last Tuesday" or "next month".
- One topic per file once files split. Lowercase, hyphen-separated names.
- Cross-references use relative paths: `[LIMS](systems/lims.md)`.
- Prefer language that survives six months. If something is genuinely in flux,
  say "under discussion as of 2026-08-18" rather than "current" or "new".
- Tables for anything with more than three parallel entries. Prose for
  everything else.
