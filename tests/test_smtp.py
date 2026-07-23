"""Tests for SMTP message construction (smtplib mocked, no network)."""

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

from zohomail.smtp import send


def _run_send(**overrides):
    """Call send() with smtplib mocked; return (result, sent_message, mock)."""
    kwargs = dict(
        from_addr="me@yourdomain.com",
        app_password="app-pass",
        to=["friend@example.com"],
        subject="Hello",
        body="Hi there!",
    )
    kwargs.update(overrides)

    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    with patch("zohomail.smtp.smtplib.SMTP_SSL", return_value=smtp) as ctor:
        result = send(**kwargs)

    smtp.login.assert_called_once_with("me@yourdomain.com", "app-pass")
    msg = smtp.send_message.call_args.args[0]
    assert isinstance(msg, EmailMessage)
    return result, msg, smtp, ctor


def test_send_basic_headers_and_result():
    result, msg, smtp, _ = _run_send()
    assert result == {"status": "sent", "to": ["friend@example.com"], "subject": "Hello"}
    assert msg["From"] == "me@yourdomain.com"
    assert msg["To"] == "friend@example.com"
    assert msg["Subject"] == "Hello"
    assert msg["Message-ID"]  # generated
    smtp.send_message.assert_called_once()


def test_send_region_selects_host():
    _, _, _, ctor_eu = _run_send(region="eu")
    assert ctor_eu.call_args.args[0] == "smtp.zoho.eu"
    _, _, _, ctor_com = _run_send(region="com")
    assert ctor_com.call_args.args[0] == "smtp.zoho.com"


def test_send_cc_added_to_recipients():
    result, msg, smtp, _ = _run_send(cc=["cc@example.com"])
    assert msg["Cc"] == "cc@example.com"
    # cc must be delivered to as well
    to_addrs = smtp.send_message.call_args.kwargs["to_addrs"]
    assert "cc@example.com" in to_addrs and "friend@example.com" in to_addrs
    assert result["to"] == ["friend@example.com", "cc@example.com"]


def test_send_reply_sets_threading_headers():
    _, msg, _, _ = _run_send(in_reply_to="<abc@zoho>")
    assert msg["In-Reply-To"] == "<abc@zoho>"
    assert msg["References"] == "<abc@zoho>"  # defaults to in_reply_to


def test_send_html_adds_alternative():
    _, msg, _, _ = _run_send(html=True, body="<b>rich</b>")
    # multipart/alternative with an HTML part present
    assert msg.is_multipart()
    subtypes = [part.get_content_subtype() for part in msg.iter_parts()]
    assert "html" in subtypes
