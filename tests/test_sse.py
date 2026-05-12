"""Tests for the Server-Sent Events frame parser.

We pin the wire-format semantics callers actually depend on:

  - one frame is terminated by a blank line, fields by newline
  - multi-line ``data:`` values are joined by '\\n' per the SSE spec
  - ``event:`` and ``id:`` default to None / "" if absent
  - ``:`` comments (keepalive heartbeats) are skipped
  - the parser handles an unfinished trailing frame without dropping data
  - it works on both a sync iterator and an async iterator of lines
"""

from __future__ import annotations

from anyframe._sse import SSEEvent, parse_sse, parse_sse_async


def _lines(*frames: str) -> list[str]:
    """Concatenate frame strings, split by newline — like httpx.iter_lines()."""
    return ("".join(frames)).split("\n")


def test_parses_a_single_frame():
    lines = _lines("event: line\ndata: hello\nid: 1\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event="line", data="hello", id="1")]


def test_data_only_frame():
    lines = _lines("data: hi\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data="hi", id=None)]


def test_multiline_data_is_joined_with_newline():
    lines = _lines("data: line1\ndata: line2\ndata: line3\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data="line1\nline2\nline3", id=None)]


def test_keepalive_comment_lines_are_skipped():
    lines = _lines(": keepalive\n\n", "data: real\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data="real", id=None)]


def test_multiple_frames():
    lines = _lines(
        "event: a\ndata: 1\n\n",
        "event: b\ndata: 2\nid: 7\n\n",
    )
    events = list(parse_sse(lines))
    assert events == [
        SSEEvent(event="a", data="1", id=None),
        SSEEvent(event="b", data="2", id="7"),
    ]


def test_empty_frame_is_dropped():
    """A bare blank line with no preceding fields is not an event."""
    lines = _lines("\n\n", "data: x\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data="x", id=None)]


def test_trailing_frame_without_terminator_is_emitted():
    """If the connection ends mid-frame, callers still get the last event."""
    # No trailing \n\n — simulates an SSE stream that closed cleanly after a frame
    lines = _lines("data: tail\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data="tail", id=None)]


def test_field_value_leading_space_is_stripped_once():
    """Per spec: only the first whitespace after ':' is the value separator."""
    lines = _lines("data:  two-leading-spaces\n\n")
    events = list(parse_sse(lines))
    assert events == [SSEEvent(event=None, data=" two-leading-spaces", id=None)]


async def test_async_parser_works_against_aiter():
    async def gen():
        for line in _lines("event: x\ndata: 1\n\n", "data: 2\n\n"):
            yield line

    events = [e async for e in parse_sse_async(gen())]
    assert events == [
        SSEEvent(event="x", data="1", id=None),
        SSEEvent(event=None, data="2", id=None),
    ]


def test_sse_event_can_decode_json_data():
    """Convenience: callers typically want the data field as JSON."""
    event = SSEEvent(event="line", data='{"a": 1}', id=None)
    assert event.json() == {"a": 1}


def test_sse_event_json_returns_none_for_empty_data():
    event = SSEEvent(event="keepalive", data="", id=None)
    assert event.json() is None
