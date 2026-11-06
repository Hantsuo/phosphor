"""
Tests for the telnet bridge: byte-level parsing, no sockets.
"""

from app.telnet import split_keys

IAC = 0xFF


def test_plain_letters() -> None:
    assert split_keys(b"look\r") == list("look") + ["\r"]


def test_crlf_is_one_enter() -> None:
    assert split_keys(b"n\r\n") == ["n", "\r"]
    assert split_keys(b"n\r\x00") == ["n", "\r"]


def test_backspace_bytes() -> None:
    assert split_keys(b"ab\x08\x7f") == ["a", "b", "\x7f", "\x7f"]


def test_iac_negotiation_is_stripped() -> None:
    data = bytes([IAC, 0xFB, 0x01]) + b"n" + bytes([IAC, 0xFD, 0x03]) + b"\r"
    assert split_keys(data) == ["n", "\r"]


def test_subnegotiation_is_stripped() -> None:
    data = bytes([IAC, 0xFA, 0x1F, 0x00, 0x50, 0x00, 0x18, IAC, 0xF0]) + b"x"
    assert split_keys(data) == ["x"]


def test_escaped_iac_survives() -> None:
    assert split_keys(bytes([IAC, IAC])) == ["\xff"]
