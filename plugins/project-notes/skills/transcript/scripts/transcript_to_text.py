#!/usr/bin/env python3
"""
Convert a meeting transcript into clean, speaker-attributed plain text.

Recognized inputs:

  .vtt    WebVTT, as Teams exports it. Preferred: a fraction of the size
          of the .docx, because the .docx embeds everyone's profile
          picture. Carries no recording date anywhere.
  .docx   The Word transcript Teams offers most prominently. Names its
          recording date in the header.
  .txt    Already-transcribed text, passed through with line endings
  .md     normalized. Speakers are recovered from the rendered headers,
          so a file that does not use the "Speaker [M:SS]" convention
          simply reports no speakers.

Every format reduces to the same shape: a blank line, a
"Speaker [timestamp]" header, then the lines of what was said. That text
is the only thing anything downstream reads, so the formats have to agree.

Two modes:

    transcript_to_text.py PATH [-o OUT] [--json] [--drop-header]
    transcript_to_text.py --find DIR [--name BASE] [--json]

The second mode only lists the transcript candidates in one directory,
best first, so a caller can apply its own policy about which to use.

Usage:
    ./transcript_to_text.py meeting.vtt
    ./transcript_to_text.py meeting.docx -o transcript.txt
    ./transcript_to_text.py meeting.docx --json
    ./transcript_to_text.py --find downloads/ --name "Weekly Standup"

Standard library only, so `python3 transcript_to_text.py ...` works
anywhere the executable bit did not survive being copied around.

Reading the resulting text faithfully is its own skill: see
../references/reading-transcripts.md before writing anything from it.
"""

import argparse
import datetime
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Formats worth discovering by globbing a directory. Plain text is
# accepted when named explicitly but never guessed at, since a directory
# full of .txt files says nothing about which one is a transcript.
TRANSCRIPT_SUFFIXES = (".vtt", ".docx")  # .vtt wins when both are present
PASSTHROUGH_SUFFIXES = (".txt", ".md")

# A line break or a run of text inside a Word paragraph.
TOKEN_RE = re.compile(r"<w:br\b[^>]*/?>|<w:t[^>]*>(.*?)</w:t>", re.DOTALL)

# The start time of a WebVTT cue, with the hour field optional.
CUE_TIMING_RE = re.compile(r"^(?:(\d+):)?([0-5]?\d):([0-5]?\d)[.,](\d{1,3})\s*-->")

# A WebVTT voice span, which is where Teams puts the speaker's name:
# <v Rivera, Dana M.>text</v>. Cue-setting classes may follow the "v".
VOICE_RE = re.compile(r"<v(?:\.[^\s.>]+)*\s+([^>]*)>")

# Any cue tag: the voice span, styling spans, inline timestamps.
CUE_TAG_RE = re.compile(r"<[^>]*>")

# "Speaker Name: what they said", the fallback for transcripts that carry
# no voice spans at all.
SPEAKER_PREFIX_RE = re.compile(r"^([A-Z][^:<>]{1,58}):\s+(.+)$")

# Blocks in a WebVTT file that are never cues.
VTT_NON_CUE_PREFIXES = ("WEBVTT", "NOTE", "STYLE", "REGION")

# The "Speaker  M:SS" first line of a .docx utterance paragraph.
DOCX_HEAD_RE = re.compile(r"^(.*?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)$")

# A rendered "Speaker [M:SS]" header, for recovering speakers from text
# that was never parsed structurally.
RENDERED_HEAD_RE = re.compile(r"^(.+?) \[\d{1,2}:\d{2}(?::\d{2})?\]$", re.MULTILINE)


class TranscriptError(Exception):
    """Indicates a transcript that cannot be read."""


@dataclass
class Transcript:
    """The result of converting one transcript file."""

    source: Path
    format: str
    text: str
    speakers: List[str]
    recording_date: Optional[datetime.date]

    def as_dict(self) -> Dict:
        """Render as JSON-ready data, dates as ISO strings."""
        return {
            "source": str(self.source),
            "format": self.format,
            "speakers": self.speakers,
            "line_count": self.text.count("\n"),
            "recording_date": (
                str(self.recording_date) if self.recording_date else None
            ),
            "text": self.text,
        }


def main():
    args = parse_args()
    try:
        if args.find:
            emit_candidates(args)
        else:
            emit_transcript(args)
    except TranscriptError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


# Main API


def convert(path: Path, drop_header: bool = False) -> Transcript:
    """Convert a transcript file into clean text plus its speakers.

    The recording date comes back only from a format that carries one,
    and only when it is actually there; a Teams .vtt has none anywhere,
    and a .docx from some other source may not either. A caller that
    needs the date to be certain has to treat None as its own answer.
    """
    suffix = path.suffix.lower()
    if suffix == ".vtt":
        text, speakers = vtt_to_text(path)
        return Transcript(path, "vtt", text, speakers, None)
    if suffix == ".docx":
        text, speakers = docx_to_text(path, drop_header=drop_header)
        return Transcript(path, "docx", text, speakers, extract_docx_date(path))
    if suffix in PASSTHROUGH_SUFFIXES:
        text, speakers = passthrough_to_text(path)
        return Transcript(path, suffix.lstrip("."), text, speakers, None)
    supported = ", ".join(TRANSCRIPT_SUFFIXES + PASSTHROUGH_SUFFIXES)
    raise TranscriptError(
        f"{path} is not a supported transcript format. Expected one of: {supported}."
    )


def find_transcripts(directory: Path, base: Optional[str] = None) -> List[Path]:
    """Return the transcript candidates in a directory, best first.

    A conventional name, when the caller knows one, wins outright — that
    is what keeps a cluttered downloads directory from looking
    ambiguous. Otherwise every candidate is returned and the caller
    decides, because a tool that guesses here guesses wrong silently.
    """
    if not directory.is_dir():
        return []
    if base:
        for suffix in TRANSCRIPT_SUFFIXES:
            conventional = directory / f"{base}{suffix}"
            if conventional.is_file():
                return [conventional]
    return [
        path
        for suffix in TRANSCRIPT_SUFFIXES
        for path in sorted(directory.glob(f"*{suffix}"))
        if path.is_file()
    ]


# WebVTT


def vtt_to_text(path: Path) -> Tuple[str, List[str]]:
    """Convert a transcript .vtt into clean text and its speakers.

    Teams breaks a single speaker turn into several short cues, so
    consecutive cues from one speaker are coalesced under one header
    rather than repeating the speaker every few seconds.
    """
    lines: List[str] = []
    speakers: List[str] = []
    speaker = None
    for cue_speaker, timestamp, text in parse_vtt_cues(path):
        if not text:
            continue
        if cue_speaker and cue_speaker != speaker:
            speaker = cue_speaker
            speakers.append(speaker)
            lines.append("")
            lines.append(f"{speaker} [{timestamp}]")
        lines.append(text)
    return render(lines), sorted(set(speakers))


def parse_vtt_cues(path: Path) -> List[Tuple[Optional[str], str, str]]:
    """Return (speaker, timestamp, text) for every cue in a WebVTT file.

    The speaker is None when a cue names nobody, which leaves its text
    attributed to whoever was speaking before it.
    """
    blocks = re.split(r"\r?\n[ \t]*\r?\n", read_vtt_text(path))
    cues = []
    for block in blocks:
        block_lines = [line.strip() for line in block.strip().splitlines()]
        if not block_lines or block_lines[0].startswith(VTT_NON_CUE_PREFIXES):
            continue
        timing = next((i for i, line in enumerate(block_lines) if "-->" in line), None)
        if timing is None:
            continue
        match = CUE_TIMING_RE.match(block_lines[timing])
        if not match:
            continue
        payload = " ".join(line for line in block_lines[timing + 1 :] if line)
        cues.append((payload, format_offset(match)))
    labelled = any(VOICE_RE.search(payload) for payload, _ in cues)
    parsed = []
    for payload, timestamp in cues:
        speaker, text = split_speaker(payload, voice_only=labelled)
        parsed.append((speaker, timestamp, text))
    return parsed


def read_vtt_text(path: Path) -> str:
    """Read a WebVTT file, refusing anything that is not one."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        raise TranscriptError(f"{path} is not a readable .vtt file: {e}") from e
    if not text.lstrip().startswith("WEBVTT"):
        raise TranscriptError(
            f"{path} does not begin with WEBVTT, so it is not a WebVTT "
            f"transcript. Export the transcript again as .vtt or .docx."
        )
    return text


def split_speaker(payload: str, voice_only: bool) -> Tuple[Optional[str], str]:
    """Split a cue payload into its speaker, if named, and its text.

    Teams names the speaker in a voice span, already in the "Last, First"
    form. When a file uses voice spans nowhere, fall back to a "Name: "
    prefix; when it uses them anywhere, never guess from a colon, since
    ordinary speech is full of them.
    """
    match = VOICE_RE.search(payload)
    if match:
        return match.group(1).strip(), strip_cue_tags(payload)
    if not voice_only:
        match = SPEAKER_PREFIX_RE.match(payload)
        if match:
            return match.group(1).strip(), strip_cue_tags(match.group(2))
    return None, strip_cue_tags(payload)


def strip_cue_tags(text: str) -> str:
    """Remove WebVTT cue tags and resolve entities, in that order."""
    return unescape(CUE_TAG_RE.sub("", text)).strip()


def format_offset(match: re.Match) -> str:
    """Render a matched cue start time the way .docx transcripts do.

    M:SS while under an hour, then H:MM:SS.
    """
    hours, minutes, seconds = (int(g or 0) for g in match.groups()[:3])
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


# Word


def docx_to_text(path: Path, drop_header: bool = False) -> Tuple[str, List[str]]:
    """Convert a transcript .docx into clean text and its speakers.

    Each utterance becomes a "Speaker [timestamp]" line followed by the
    lines of what was said. Profile-picture artifacts and empty
    paragraphs are dropped.

    Teams also writes a few header paragraphs naming the recording before
    any speaker turn. They are kept by default, because every transcript
    filed so far includes them; drop_header discards everything up to the
    first speaker.
    """
    lines: List[str] = []
    speakers: List[str] = []
    started = False
    for paragraph in iter_paragraphs(path):
        paragraph = paragraph.strip()
        if not paragraph or re.fullmatch(r"[\d\s:]+", paragraph):
            continue
        parts = paragraph.split("\n")
        head = DOCX_HEAD_RE.match(parts[0])
        if head:
            speaker, timestamp = head.group(1).strip(), head.group(2)
            started = True
            speakers.append(speaker)
            lines.append("")
            lines.append(f"{speaker} [{timestamp}]")
            parts = parts[1:]
        elif drop_header and not started:
            continue
        lines.extend(p.strip() for p in parts if p.strip())
    return render(lines), sorted(set(speakers))


def extract_docx_date(path: Path) -> Optional[datetime.date]:
    """Read the recording date out of a .docx transcript's header.

    Returns None when there is none to find. Only a caller that needs
    the date as a safety check can decide that its absence is an error.
    """
    header = "\n".join(iter_paragraphs(path)[:4])
    match = re.search(r"-(\d{4})(\d{2})(\d{2})_\d{6}-", header)
    if match:
        return datetime.date(*(int(g) for g in match.groups()))
    match = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", header)
    if match:
        return datetime.datetime.strptime(match.group(1), "%B %d, %Y").date()
    return None


def iter_paragraphs(path: Path) -> List[str]:
    """Return the text of each paragraph, with line breaks preserved.

    Word stores each transcript line as a run separated by <w:br/>, so
    those become newlines within the returned paragraph.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError) as e:
        raise TranscriptError(f"{path} is not a readable .docx file: {e}") from e
    paragraphs = []
    for block in re.findall(r"<w:p[ >].*?</w:p>", xml, re.DOTALL):
        pieces = [
            "\n" if match.group(1) is None else match.group(1)
            for match in TOKEN_RE.finditer(block)
        ]
        paragraphs.append(unescape("".join(pieces)))
    return paragraphs


# Plain text


def passthrough_to_text(path: Path) -> Tuple[str, List[str]]:
    """Normalize already-transcribed text, recovering any speakers."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        raise TranscriptError(f"{path} is not a readable text file: {e}") from e
    text = render(raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    return text, list_speakers(text)


def list_speakers(text: str) -> List[str]:
    """Return the speaker labels appearing in already-rendered text.

    A fallback for text nothing parsed structurally. Prefer the speakers
    a converter collected while rendering, which cannot mistake a line of
    speech for a header.
    """
    return sorted(set(RENDERED_HEAD_RE.findall(text)))


# Output


def emit_transcript(args) -> None:
    """Convert one transcript and write it out."""
    if not args.path.is_file():
        raise TranscriptError(f"No such transcript: {args.path}")
    transcript = convert(args.path, drop_header=args.drop_header)
    if args.output:
        args.output.write_text(transcript.text, encoding="utf-8")
    if args.json:
        print(json.dumps(transcript.as_dict(), indent=2))
    elif not args.output:
        sys.stdout.write(transcript.text)


def emit_candidates(args) -> None:
    """List the transcript candidates in a directory, best first."""
    candidates = find_transcripts(args.find, args.name)
    if args.json:
        print(
            json.dumps(
                {
                    "directory": str(args.find),
                    "candidates": [str(path) for path in candidates],
                },
                indent=2,
            )
        )
        return
    for path in candidates:
        print(path)


def render(lines: List[str]) -> str:
    """Join rendered lines into a transcript body."""
    return "\n".join(lines).strip() + "\n"


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", type=Path, nargs="?", help="Transcript to convert")
    parser.add_argument(
        "-o", "--output", type=Path, help="Write the text here instead of stdout"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary (source, format, speakers, recording date, text)",
    )
    parser.add_argument(
        "--drop-header",
        action="store_true",
        help="Discard the .docx recording header before the first speaker",
    )
    parser.add_argument(
        "--find",
        type=Path,
        metavar="DIR",
        help="List the transcript candidates in DIR instead of converting",
    )
    parser.add_argument(
        "--name",
        help="Conventional transcript base name, which wins outright in --find",
    )
    args = parser.parse_args()
    if args.find and args.path:
        parser.error("--find lists a directory; it takes no transcript to convert.")
    if not args.find and not args.path:
        parser.error("Name a transcript to convert, or a directory with --find.")
    return args


if __name__ == "__main__":
    main()
