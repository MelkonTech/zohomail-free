"""zohomail-free — Zoho Mail client for free-tier accounts.

Provides programmatic access to Zoho Mail without IMAP or POP3,
which are locked behind Zoho's paid plans. Uses Playwright to
authenticate via the web UI and communicates with Zoho's internal
JSON API directly.

Quickstart:
    >>> import asyncio
    >>> from zohomail.client import ZohoMailClient
    >>>
    >>> client = ZohoMailClient(
    ...     email="you@yourdomain.com",
    ...     password="your_password",
    ...     region="eu",
    ... )
    >>> emails = asyncio.run(client.list_emails(limit=5))
    >>> for e in emails:
    ...     print(e["subject"])

Public API:
    - :class:`~zohomail.client.ZohoMailClient` — read emails
    - :func:`~zohomail.smtp.send` — send / reply via SMTP
    - :class:`~zohomail.client.ZohoMailError` — base exception
    - :class:`~zohomail.client.SessionExpiredError` — session error
"""

from zohomail.client import ZohoMailClient, ZohoMailError, SessionExpiredError
from zohomail.smtp import send

__version__ = "0.1.0"
__all__ = ["ZohoMailClient", "ZohoMailError", "SessionExpiredError", "send"]
