"""Tests for transcript_to_text.

Every format has to reduce to the same plain-text shape, because that
text is the only thing anything downstream reads.
"""

import datetime
import json
import subprocess
import sys
import zipfile
from html import escape
from pathlib import Path

import pytest
from transcript_to_text import (
    TranscriptError,
    convert,
    docx_to_text,
    extract_docx_date,
    find_transcripts,
    list_speakers,
    passthrough_to_text,
    vtt_to_text,
)

FIXTURES = Path(__file__).parent / "fixtures"
TOOL = Path(__file__).resolve().parent.parent / "scripts" / "transcript_to_text.py"

# What sample.vtt must reduce to: consecutive cues from one speaker
# coalesced under a single header, entities resolved, an unattributed cue
# left with whoever was speaking, and H:MM:SS past the hour mark.
EXPECTED_VTT_TEXT = """\
Rivera, Dana M. [0:03]
She put her likeness in a...
Whatever that tool is, make her own avatar.

Hale, Walker [0:09]
Oh, yeah, I don't know about that.
Is 3 < 5 & 5 > 3?
An aside that names nobody.

Rivera, Dana M. [1:02:03]
Wrapping up, an hour in.
"""

RECORDING_HEADER = "Weekly Standup-20260723_120101-Meeting Recording"

EXPECTED_DOCX_BODY = (
    "Rivera, Dana M. [0:03]\n"
    "She put her likeness in a...\n"
    "Whatever that tool is,\n"
    "make her own avatar.\n"
    "\n"
    "Hale, Walker [0:09]\n"
    "Oh, yeah, I don't know about that.\n"
    "Is 3 < 5 & 5 > 3?\n"
)

EXPECTED_DOCX_TEXT = (
    f"{RECORDING_HEADER}\nJuly 23, 2026, 5:01PM\n\n{EXPECTED_DOCX_BODY}"
)


# Format conversion


def test_vtt_to_text_matches_expected_shape(sample_vtt):
    text, speakers = vtt_to_text(sample_vtt)
    assert text == EXPECTED_VTT_TEXT
    assert speakers == ["Hale, Walker", "Rivera, Dana M."]


def test_docx_to_text_matches_expected_shape(sample_docx):
    """The header paragraphs survive; the profile-picture digits do not."""
    text, speakers = docx_to_text(sample_docx)
    assert text == EXPECTED_DOCX_TEXT
    assert speakers == ["Hale, Walker", "Rivera, Dana M."]


def test_both_formats_yield_the_same_speakers(sample_vtt, sample_docx):
    assert docx_to_text(sample_docx)[1] == vtt_to_text(sample_vtt)[1]


def test_docx_can_drop_the_recording_header(sample_docx):
    assert docx_to_text(sample_docx, drop_header=True)[0] == EXPECTED_DOCX_BODY


def test_convert_dispatches_on_suffix(sample_vtt, sample_docx):
    assert convert(sample_vtt).text == vtt_to_text(sample_vtt)[0]
    assert convert(sample_docx).text == docx_to_text(sample_docx)[0]
    assert convert(sample_vtt).format == "vtt"
    assert convert(sample_docx).format == "docx"


def test_convert_reports_the_recording_date_only_where_there_is_one(
    sample_vtt, sample_docx
):
    assert convert(sample_docx).recording_date == datetime.date(2026, 7, 23)
    assert convert(sample_vtt).recording_date is None


def test_convert_rejects_an_unsupported_format(tmp_path):
    path = tmp_path / "slides.pptx"
    path.write_bytes(b"")
    with pytest.raises(TranscriptError, match="not a supported transcript format"):
        convert(path)


# Plain text passthrough


def test_passthrough_normalizes_line_endings_and_finds_speakers(tmp_path):
    path = tmp_path / "already.txt"
    path.write_text(
        "Hale, Walker [0:01]\r\nFirst thing.\r\n\r\nRivera, Dana M. [0:05]\r\nNext.\r\n",
        encoding="utf-8",
        newline="",
    )
    text, speakers = passthrough_to_text(path)
    assert "\r" not in text
    assert speakers == ["Hale, Walker", "Rivera, Dana M."]


def test_passthrough_without_headers_reports_no_speakers(tmp_path):
    path = tmp_path / "prose.md"
    path.write_text("Just some notes about a call.\n", encoding="utf-8")
    assert passthrough_to_text(path) == ("Just some notes about a call.\n", [])


def test_list_speakers_reads_rendered_headers():
    assert list_speakers(EXPECTED_VTT_TEXT) == [
        "Hale, Walker",
        "Rivera, Dana M.",
    ]


# VTT specifics


def test_vtt_coalesces_a_speaker_run(sample_vtt):
    text, _ = vtt_to_text(sample_vtt)
    assert text.count("Hale, Walker [") == 1
    assert text.count("Rivera, Dana M. [") == 2  # returns after Walker speaks


def test_vtt_falls_back_to_a_name_prefix_when_no_voice_spans(tmp_path):
    path = tmp_path / "plain.vtt"
    path.write_text(
        "WEBVTT\n\n"
        "1\n00:00:01.000 --> 00:00:02.000\nHale, Walker: First thing.\n\n"
        "2\n00:00:03.000 --> 00:00:04.000\nRivera, Dana M.: Second thing.\n",
        encoding="utf-8",
    )
    assert vtt_to_text(path)[0] == (
        "Hale, Walker [0:01]\nFirst thing.\n\n"
        "Rivera, Dana M. [0:03]\nSecond thing.\n"
    )


def test_vtt_never_guesses_a_speaker_from_speech_containing_a_colon(tmp_path):
    """A file that uses voice spans must not read a colon as a speaker."""
    path = tmp_path / "colon.vtt"
    path.write_text(
        "WEBVTT\n\n"
        "1\n00:00:01.000 --> 00:00:02.000\n<v Hale, Walker>Here is the thing:</v>\n\n"
        "2\n00:00:03.000 --> 00:00:04.000\nSo here is the thing: we ship it.\n",
        encoding="utf-8",
    )
    text, speakers = vtt_to_text(path)
    assert speakers == ["Hale, Walker"]
    assert "we ship it." in text


def test_vtt_tolerates_a_byte_order_mark(tmp_path):
    path = tmp_path / "bom.vtt"
    path.write_text(
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:02.000\n<v A>Hi.</v>\n",
        encoding="utf-8-sig",
    )
    assert vtt_to_text(path)[0] == "A [0:01]\nHi.\n"


def test_vtt_without_the_webvtt_header_is_rejected(tmp_path):
    path = tmp_path / "not-really.vtt"
    path.write_text("1\n00:00:01.000 --> 00:00:02.000\nHello.\n", encoding="utf-8")
    with pytest.raises(TranscriptError, match="WEBVTT"):
        vtt_to_text(path)


def test_a_speaker_run_past_a_hundred_minutes_is_still_a_header(tmp_path):
    """The rendered header rolls to H:MM:SS, so speakers stay recoverable."""
    path = tmp_path / "long.vtt"
    path.write_text(
        "WEBVTT\n\n1\n01:45:06.000 --> 01:45:08.000\n<v Hale, Walker>Still here.</v>\n",
        encoding="utf-8",
    )
    text, speakers = vtt_to_text(path)
    assert text == "Hale, Walker [1:45:06]\nStill here.\n"
    assert speakers == list_speakers(text)


# Dates


def test_extract_docx_date_from_the_recording_stamp(sample_docx):
    assert extract_docx_date(sample_docx) == datetime.date(2026, 7, 23)


def test_extract_docx_date_from_a_written_date(tmp_path):
    path = build_docx(tmp_path / "written.docx", ["July 23, 2026, 5:01PM"])
    assert extract_docx_date(path) == datetime.date(2026, 7, 23)


def test_extract_docx_date_without_a_date_is_none(tmp_path):
    """Absence is an answer here; only a caller can call it an error."""
    path = build_docx(tmp_path / "undated.docx", ["Meeting Recording"])
    assert extract_docx_date(path) is None


def test_a_docx_that_is_not_a_zip_is_rejected(tmp_path):
    path = tmp_path / "fake.docx"
    path.write_text("not a zip", encoding="utf-8")
    with pytest.raises(TranscriptError, match="not a readable .docx"):
        docx_to_text(path)


# Discovery


def test_find_transcripts_prefers_the_conventional_name(downloads):
    touch(downloads / "some-other-thing.docx")
    touch(downloads / "unrelated.vtt")
    conventional = touch(downloads / "Weekly Standup.docx")
    assert find_transcripts(downloads, "Weekly Standup") == [conventional]


def test_find_transcripts_prefers_vtt_under_the_conventional_name(downloads):
    touch(downloads / "Weekly Standup.docx")
    preferred = touch(downloads / "Weekly Standup.vtt")
    assert find_transcripts(downloads, "Weekly Standup") == [preferred]


def test_find_transcripts_returns_every_candidate_without_a_convention(downloads):
    docx = touch(downloads / "one.docx")
    vtt = touch(downloads / "two.vtt")
    assert find_transcripts(downloads) == [vtt, docx]


def test_find_transcripts_ignores_unrelated_files(downloads):
    touch(downloads / "notes.txt")
    touch(downloads / "slides.pptx")
    assert find_transcripts(downloads) == []


def test_find_transcripts_in_a_missing_directory(tmp_path):
    assert find_transcripts(tmp_path / "nope") == []


# The command line, which is how other skills reach this tool


def test_cli_writes_text_to_stdout(sample_vtt):
    assert run_tool(str(sample_vtt)).stdout == EXPECTED_VTT_TEXT


def test_cli_json_carries_the_whole_summary(sample_docx):
    summary = json.loads(run_tool(str(sample_docx), "--json").stdout)
    assert summary["format"] == "docx"
    assert summary["recording_date"] == "2026-07-23"
    assert summary["speakers"] == ["Hale, Walker", "Rivera, Dana M."]
    assert summary["text"] == EXPECTED_DOCX_TEXT
    assert summary["line_count"] == EXPECTED_DOCX_TEXT.count("\n")


def test_cli_output_flag_writes_a_file(sample_vtt, tmp_path):
    out = tmp_path / "transcript.txt"
    result = run_tool(str(sample_vtt), "-o", str(out))
    assert out.read_text(encoding="utf-8") == EXPECTED_VTT_TEXT
    assert result.stdout == ""


def test_cli_find_lists_candidates_as_json(downloads):
    vtt = touch(downloads / "Weekly Standup.vtt")
    touch(downloads / "other.docx")
    found = json.loads(
        run_tool("--find", str(downloads), "--name", "Weekly Standup", "--json").stdout
    )
    assert found == {"directory": str(downloads), "candidates": [str(vtt)]}


def test_cli_reports_a_missing_transcript_on_stderr(tmp_path):
    result = run_tool(str(tmp_path / "gone.vtt"), check=False)
    assert result.returncode == 1
    assert "No such transcript" in result.stderr


def test_cli_refuses_to_convert_and_find_at_once(sample_vtt, downloads):
    result = run_tool(str(sample_vtt), "--find", str(downloads), check=False)
    assert result.returncode == 2


def test_cli_needs_something_to_do():
    assert run_tool(check=False).returncode == 2


# Fixtures and helpers


@pytest.fixture
def sample_vtt() -> Path:
    return FIXTURES / "sample.vtt"


@pytest.fixture
def sample_docx(tmp_path) -> Path:
    """A .docx shaped the way Teams writes one.

    Teams puts each utterance in one paragraph, its first line being
    "Speaker  M:SS", and litters the document with paragraphs of bare
    digits where profile pictures were.
    """
    return build_docx(
        tmp_path / "Weekly Standup.docx",
        [
            RECORDING_HEADER,
            "July 23, 2026, 5:01PM",
            "0:00",
            "Rivera, Dana M.  0:03\nShe put her likeness in a...\n"
            "Whatever that tool is,\nmake her own avatar.",
            "12 34",
            "Hale, Walker  0:09\nOh, yeah, I don't know about that.\nIs 3 < 5 & 5 > 3?",
        ],
    )


@pytest.fixture
def downloads(tmp_path) -> Path:
    path = tmp_path / "Downloads"
    path.mkdir()
    return path


def run_tool(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Invoke the tool as a subprocess, the way other skills do.

    Runs it under this interpreter rather than relying on the shebang,
    so the tests exercise the same `python3 script.py` form a sandbox
    without the executable bit would use.
    """
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def build_docx(path: Path, paragraphs: list) -> Path:
    """Write a minimal .docx whose body is the given paragraphs.

    Newlines within a paragraph become <w:br/>, which is how Word stores
    the lines of one utterance and what the parser reads.
    """
    body = "".join(paragraph_xml(paragraph) for paragraph in paragraphs)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<w:document "
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return path


def paragraph_xml(text: str) -> str:
    runs = "<w:br/>".join(
        f'<w:t xml:space="preserve">{escape(line, quote=False)}</w:t>'
        for line in text.split("\n")
    )
    return f"<w:p>{runs}</w:p>"


def touch(path: Path) -> Path:
    path.write_bytes(b"")
    return path
