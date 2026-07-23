"""Tests for HTML stripping and attachment parsing (no network required)."""

from zohomail.client import strip_html, _parse_attachments


def test_strip_html_removes_tags():
    out = strip_html("<p>Hello <b>world</b></p>")
    assert "Hello" in out
    assert "world" in out
    assert "<" not in out and ">" not in out


def test_strip_html_empty():
    assert strip_html("") == ""


def test_parse_attachments_none():
    assert _parse_attachments({}) == []
    assert _parse_attachments({"NEWATT": None}) == []


def test_parse_attachments_basic():
    md = {
        "NEWATT": [
            {"fn": "invoice.pdf", "fmt": "pdf", "fs": "20480",
             "part": "2", "id": "att123", "inline": False},
            "not-a-dict",  # should be skipped
            {"fn": "logo.png", "fmt": "png", "fs": "bad-size", "inline": True},
        ]
    }
    atts = _parse_attachments(md)
    assert len(atts) == 2

    first = atts[0]
    assert first["name"] == "invoice.pdf"
    assert first["format"] == "pdf"
    assert first["size_bytes"] == 20480
    assert first["part_id"] == "2"
    assert first["attachment_id"] == "att123"
    assert first["inline"] is False

    second = atts[1]
    assert second["name"] == "logo.png"
    assert second["size_bytes"] == 0  # unparseable size falls back to 0
    assert second["inline"] is True
