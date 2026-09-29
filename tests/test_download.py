"""Tests for the pure helpers behind attachment downloading (no network)."""

from zohomail.client import _safe_filename, _unique_path, _ssl_context


def test_safe_filename_strips_separators():
    assert "/" not in _safe_filename("../../etc/passwd", "x")
    assert _safe_filename("", "attachment-1") == "attachment-1"
    assert _safe_filename("slides.pdf", "x") == "slides.pdf"


def test_unique_path_suffixes_duplicates(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"1")
    assert _unique_path(tmp_path, "a.pdf").name == "a (1).pdf"
    (tmp_path / "a (1).pdf").write_bytes(b"2")
    assert _unique_path(tmp_path, "a.pdf").name == "a (2).pdf"


def test_ssl_context_verifies():
    import ssl
    assert _ssl_context().verify_mode == ssl.CERT_REQUIRED
