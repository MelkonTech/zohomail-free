"""zohomail-free — Read, send, and reply to Zoho Mail emails on free-tier accounts.

Zoho locks IMAP/POP3 behind paid plans, so standard email libraries
don't work on free accounts. This library authenticates via the Zoho
web UI and communicates with their internal JSON API directly — giving
you full inbox access and SMTP sending without paying for a plan.

Quickstart:
    >>> import asyncio
    >>> from zohomail import ZohoMailClient, send
    >>>
    >>> client = ZohoMailClient(
    ...     email="you@yourdomain.com",
    ...     password="your_password",
    ...     region="eu",
    ... )
    >>> emails = asyncio.run(client.list_emails(limit=5))
    >>> for e in emails:
    ...     print(e["subject"])

AI integration:
    >>> from zohomail.ai import email_to_prompt, emails_to_messages
    >>> # feed directly into OpenAI / Anthropic / any LLM SDK

Public API:
    - :class:`~zohomail.client.ZohoMailClient` — read emails
    - :func:`~zohomail.smtp.send` — send / reply via SMTP
    - :mod:`~zohomail.ai` — helpers for LLM integration
    - :class:`~zohomail.client.ZohoMailError` — base exception
    - :class:`~zohomail.client.SessionExpiredError` — session error
"""

from zohomail.client import ZohoMailClient, ZohoMailError, SessionExpiredError
from zohomail.smtp import send
from zohomail import ai  # noqa: F401 — re-export the module

__version__ = "0.1.5"
__all__ = ["ZohoMailClient", "ZohoMailError", "SessionExpiredError", "send", "ai"]
