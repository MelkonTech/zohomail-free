"""zohomail-free — Read, send, and reply to Zoho Mail emails on free-tier accounts.

Zoho locks IMAP/POP3 behind paid plans, so standard email libraries
don't work on free accounts. This library authenticates via the Zoho
web UI and communicates with their internal JSON API directly — giving
you full inbox access and SMTP sending without paying for a plan.

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

__version__ = "0.1.2"
__all__ = ["ZohoMailClient", "ZohoMailError", "SessionExpiredError", "send"]
