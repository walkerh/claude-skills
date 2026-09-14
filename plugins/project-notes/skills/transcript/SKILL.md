---
name: transcript
description: Convert a meeting or call transcript (.vtt, .docx, .txt) into clean speaker-attributed text, then read it faithfully to produce whatever the context calls for — a summary, notes, decisions, action items, or an answer about what was said. Use when the user points at a transcript or recording export, says "process this transcript", "summarize this call", "what did they say about X", or drops a .vtt or .docx transcript into a project. For the Submissions Coordination Meeting minutes workflow specifically, use the meeting-minutes skill instead.
---

# Transcript

Two things, in order: convert the file to clean text, then read that text
without embellishing it.

This skill does not decide what you produce. A transcript in a
micro-project becomes wiki facts and tasks; a transcript of a formal
meeting becomes minutes; a transcript someone hands you with a question
becomes an answer. Match the destination.

## Step 1 — Convert

```bash
scripts/transcript_to_text.py PATH --json
```

Prints a JSON summary — `source`, `format`, `speakers`, `line_count`,
`recording_date`, `text`. Without `--json` the text goes to stdout, so
the tool composes; `-o PATH` writes it to a file instead.

The script is standard library only. If direct invocation fails because
the executable bit did not survive however this skill was installed, run
`python3 scripts/transcript_to_text.py ...` instead — same arguments,
same output.

Every format reduces to the same shape: a blank line, a
`Speaker [timestamp]` header, then the lines of what was said.

| Format | Notes |
|---|---|
| `.vtt` | WebVTT, as Teams exports it. **Preferred** — a fraction of the size of the `.docx`, which embeds every participant's profile picture. Carries no recording date anywhere, so `recording_date` is null. |
| `.docx` | The Word transcript Teams offers most prominently. Names its recording date in the header, which comes back in `recording_date`. |
| `.txt`, `.md` | Already-transcribed text, passed through with line endings normalized. Speakers are recovered from `Speaker [M:SS]` headers if present, otherwise none are reported. |

The Teams `.docx` opens with a few paragraphs naming the recording,
before anyone speaks. They are kept by default; `--drop-header` discards
everything up to the first speaker.

**Do not hand-parse a transcript.** The `.vtt` speaker attribution in
particular is subtle — Teams splits one speaker turn across many short
cues, and ordinary speech is full of colons that look like speaker
labels. The script handles both and is tested against real exports.

**Finding the file.** When you know the directory but not the filename —
a downloads folder, a project `inbox/`, wherever an upload landed:

```bash
scripts/transcript_to_text.py --find DIR --json
```

Lists the `.vtt` and `.docx` candidates, best first, and nothing else.
`--name BASE` makes a known conventional filename win outright, which is
what keeps a cluttered downloads directory from looking ambiguous.
Anything past that is the caller's policy: with more than one candidate
and no convention to break the tie, ask rather than guess.

`recording_date` is null whenever there was none to find. If the date
matters — confirming the right recording was exported, for instance —
null is an answer that needs handling, not a default to paper over.

## Step 2 — Read it

Read `references/reading-transcripts.md` before writing anything from
the text. It is short, and it covers the failure modes that make
transcript-derived writing untrustworthy: who counts as present, which
garbled terms to fix silently and which to ask about, what is chatter
rather than content, and the difference between what was said and what
is true.

Then produce what the context calls for.

## Step 3 — Keep the source

A transcript is worth keeping — it is the only way to check a claim
later. Preserve it wherever the project keeps sources, with a note of
where it came from and when. Do not delete it after distilling it.
