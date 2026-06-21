"""SMTP sender for Zoho Mail.

Sends email via Zoho's SMTP server using an app-specific password.
Works on free-tier accounts — SMTP is not gated behind paid plans.

Note:
    You must generate an app-specific password in Zoho Mail →
    Settings → Security → App Passwords. Your regular login password
    will not work here.
"""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def _ssl_ctx() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def send(
    from_addr: str,
    app_password: str,
    to: list[str],
    subject: str,
    body: str,
    *,
    region: str = "eu",
    cc: list[str] | None = None,
    html: bool = False,
    in_reply_to: str = "",
    references: str = "",
) -> dict:
    """Send an email via Zoho SMTP.

    Args:
        from_addr: Sender address — must match the authenticated Zoho account.
        app_password: App-specific password generated in Zoho Security settings.
        to: List of recipient email addresses.
        subject: Email subject line.
        body: Email body — plain text, or HTML if ``html=True``.
        region: Zoho data-centre — ``"eu"`` (default) or ``"com"``.
        cc: Optional list of CC addresses.
        html: If ``True``, send ``body`` as HTML (with a plain-text fallback).
        in_reply_to: RFC 2822 ``Message-ID`` of the email being replied to.
            Sets ``In-Reply-To`` and ``References`` headers for threading.
        references: Override the ``References`` header. Defaults to
            ``in_reply_to`` when omitted.

    Returns:
        A dict with ``status``, ``to``, and ``subject`` keys::

            {"status": "sent", "to": ["a@b.com"], "subject": "Hello"}

    Raises:
        smtplib.SMTPException: On connection or authentication failure.

    Example:
        >>> from zohomail.smtp import send
        >>> send(
        ...     from_addr="you@yourdomain.com",
        ...     app_password="xxxx-xxxx",
        ...     to=["friend@example.com"],
        ...     subject="Hello",
        ...     body="Hi there!",
        ... )
    """
    host = f"smtp.zoho.{'eu' if region.lower() == 'eu' else 'com'}"
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = references or in_reply_to
    if html:
        msg.set_content("This message requires an HTML-capable client.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    recipients = list(to) + list(cc or [])
    with smtplib.SMTP_SSL(host, 465, context=_ssl_ctx()) as s:
        s.login(from_addr, app_password)
        s.send_message(msg, from_addr=from_addr, to_addrs=recipients)

    return {"status": "sent", "to": recipients, "subject": subject}
