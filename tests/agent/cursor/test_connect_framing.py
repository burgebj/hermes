from __future__ import annotations

import pytest

from agent.cursor.connect_framing import (
    frame_connect_message,
    parse_connect_end_stream,
    parse_connect_frames,
)
from agent.cursor.constants import CONNECT_END_STREAM_FLAG


def test_frame_connect_message_round_trips_through_parser():
    frame = frame_connect_message(b"hello", flags=1)
    parsed = list(parse_connect_frames(bytearray(frame)))

    assert parsed == [(1, b"hello")]


def test_parse_connect_frames_consumes_complete_frames_and_preserves_tail():
    first = frame_connect_message(b"one")
    second = frame_connect_message(b"two", flags=3)
    partial = frame_connect_message(b"three")[:6]
    buffer = bytearray(first + second + partial)

    parsed = list(parse_connect_frames(buffer))

    assert parsed == [(0, b"one"), (3, b"two")]
    assert buffer == partial


def test_parse_connect_frames_accepts_immutable_bytes():
    frame = frame_connect_message(b"payload")

    assert list(parse_connect_frames(frame)) == [(0, b"payload")]


def test_parse_connect_end_stream_returns_none_when_no_error():
    assert parse_connect_end_stream(b"{}") is None


def test_parse_connect_end_stream_surfaces_connect_error():
    error = parse_connect_end_stream(
        b'{"error":{"code":"permission_denied","message":"Missing auth"}}'
    )

    assert isinstance(error, Exception)
    assert "permission_denied" in str(error)
    assert "Missing auth" in str(error)


def test_parse_connect_end_stream_returns_parse_error_for_invalid_json():
    error = parse_connect_end_stream(b"not-json")

    assert isinstance(error, Exception)
    assert "Failed to parse Connect end stream" in str(error)


def test_end_stream_flag_can_be_round_tripped():
    frame = frame_connect_message(b'{"error":null}', flags=CONNECT_END_STREAM_FLAG)

    assert list(parse_connect_frames(bytearray(frame))) == [
        (CONNECT_END_STREAM_FLAG, b'{"error":null}')
    ]
