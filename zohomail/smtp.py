"""SMTP sender — works on Zoho free tier."""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid


def _ssl_ctx():
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
