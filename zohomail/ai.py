"""AI integration helpers for zohomail-free.

Provides lightweight utilities that make it easy to feed Zoho Mail data
into AI APIs (OpenAI, Anthropic, etc.) — no extra dependencies required.
The helpers return plain dicts and strings so you can pass them directly
to any LLM SDK.

Example — summarise inbox with OpenAI::

    from openai import OpenAI
    from zohomail import ZohoMailClient
    from zohomail.ai import emails_to_messages, email_to_prompt

    import asyncio

    client = ZohoMailClient(email="you@zoho.com", password="...", region="eu")
    emails = asyncio.run(client.list_emails(limit=10))

    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=emails_to_messages(emails, system="Summarise these emails briefly."),
    )
    print(response.choices[0].message.content)

Example — reply with Claude::

    import anthropic
    from zohomail.ai import email_to_prompt

    email = asyncio.run(client.read_email(emails[0]["id"]))

    ac = anthropic.Anthropic()
    message = ac.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": email_to_prompt(email)}],
    )
    print(message.content[0].text)
"""

from __future__ import annotations

import json
from typing import Any


def email_to_text(email: dict) -> str:
    """Convert a single read_email() result to a readable plain-text string.

    Useful for feeding an individual email into an LLM prompt.

    Args:
        email: Dict returned by :meth:`~zohomail.client.ZohoMailClient.read_email`.

    Returns:
        A formatted plain-text representation of the email.
    """
    parts = [
        f"From: {email.get('from', '')}",
        f"To: {email.get('to', '')}",
        f"Date: {email.get('date', '')}",
        f"Subject: {email.get('subject', '')}",
        "",
        email.get("body") or email.get("body_html") or "(no body)",
    ]
    return "\n".join(parts)


def email_to_prompt(email: dict, instruction: str = "Reply to this email:") -> str:
    """Build a ready-to-use LLM prompt from an email.

    Args:
        email: Dict returned by :meth:`~zohomail.client.ZohoMailClient.read_email`.
        instruction: Leading instruction line prepended to the email text.

    Returns:
        A string suitable for use as the ``content`` of an LLM user message.
    """
    return f"{instruction}\n\n{email_to_text(email)}"


def emails_to_messages(
    emails: list[dict],
    system: str = "You are an email assistant. The user's inbox is shown below.",
) -> list[dict[str, str]]:
    """Convert a list of inbox emails to an OpenAI-style messages list.

    The inbox is serialised as a JSON block in the user message so the LLM
    can reason over all emails at once.

    Args:
        emails: List returned by :meth:`~zohomail.client.ZohoMailClient.list_emails`.
        system: System prompt describing the task.

    Returns:
        A list of ``{"role": ..., "content": ...}`` dicts compatible with
        OpenAI, Anthropic (via ``system`` kwarg), and most other LLM SDKs.
    """
    inbox_json = json.dumps(emails, indent=2, ensure_ascii=False)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Inbox:\n```json\n{inbox_json}\n```"},
    ]


def email_to_tool_result(email: dict) -> dict[str, Any]:
    """Wrap an email as an Anthropic tool_result block.

    Useful when your agent calls a ``read_email`` tool and needs to return
    the result to Claude in the correct format.

    Args:
        email: Dict returned by :meth:`~zohomail.client.ZohoMailClient.read_email`.

    Returns:
        An Anthropic-compatible tool result dict with ``type``, ``content``.
    """
    return {
        "type": "tool_result",
        "content": email_to_text(email),
    }
