"""FastAPI REST server for zohomail-free.

Exposes Zoho Mail operations over HTTP with API key authentication.
Intended for self-hosting — run locally or deploy via Docker/Railway.

Endpoints:
    GET  /health              — liveness check
    GET  /emails              — list inbox (``?limit=10``)
    GET  /emails/{id}         — read full email
    POST /emails/send         — send new email
    POST /emails/{id}/reply   — reply to an email

Authentication:
    Every request (except ``/health``) must include an
    ``X-API-Key: <your_key>`` header. Set ``API_KEY`` in your ``.env``.

Example::

    curl -H "X-API-Key: your_key" http://localhost:8000/emails
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from zohomail.client import ZohoMailClient
from zohomail.smtp import send as smtp_send

API_KEY      = os.environ.get("API_KEY", "changeme")
EMAIL        = os.environ.get("ZOHO_EMAIL", "")
PASSWORD     = os.environ.get("ZOHO_PASSWORD", "")
APP_PASSWORD = os.environ.get("ZOHO_APP_PASSWORD", "")
REGION       = os.environ.get("ZOHO_REGION", "eu")

app = FastAPI(
    title="zohomail-free API",
    description=(
        "Zoho Mail REST API for free-tier accounts — no IMAP needed.\n\n"
        "Built by [MelkonTech](https://melkon.tech/Melkon.Tech/ai/)"
    ),
    version="0.1.0",
    contact={
        "name": "MelkonTech",
        "url": "https://melkon.tech/Melkon.Tech/ai/",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/MelkonTech/zohomail-free/blob/main/LICENSE",
    },
)


def _auth(x_api_key: str = Header(...)):
    """Validate the X-API-Key header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _client() -> ZohoMailClient:
    return ZohoMailClient(email=EMAIL, password=PASSWORD, region=REGION)


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health", summary="Health check")
async def health():
    """Return service status. No auth required."""
    return {"status": "ok"}


@app.get("/emails", summary="List inbox messages")
async def list_emails(
    limit: int = Query(10, le=50, description="Number of messages to return"),
    x_api_key: str = Header(...),
):
    """Return the most recent ``limit`` inbox messages, newest first.

    Each item contains ``id``, ``from``, ``subject``, ``time_ms``, ``unread``.
    Pass ``id`` to ``GET /emails/{id}`` to read the full message.
    """
    _auth(x_api_key)
    return await _client().list_emails(limit=limit)


@app.get("/emails/{msg_id}", summary="Read a full email")
async def read_email(msg_id: str, x_api_key: str = Header(...)):
    """Return the full content of a single email by its Zoho message ID.

    Includes ``from``, ``reply_to``, ``to``, ``date``, ``subject``,
    ``message_id`` (for threading), ``body`` (plain text), and ``body_html``.
    """
    _auth(x_api_key)
    return await _client().read_email(msg_id)


class SendRequest(BaseModel):
    """Request body for sending a new email."""

    to: list[str]
    """List of recipient email addresses."""

    subject: str
    """Email subject line."""

    body: str
    """Email body — plain text, or HTML if ``html`` is true."""

    cc: list[str] = []
    """Optional CC addresses."""

    html: bool = False
    """Set to ``true`` to send ``body`` as HTML."""


@app.post("/emails/send", summary="Send a new email")
async def send_email(req: SendRequest, x_api_key: str = Header(...)):
    """Compose and send a new email via Zoho SMTP."""
    _auth(x_api_key)
    return smtp_send(
        from_addr=EMAIL, app_password=APP_PASSWORD,
        to=req.to, subject=req.subject, body=req.body,
        region=REGION, cc=req.cc, html=req.html,
    )


class ReplyRequest(BaseModel):
    """Request body for replying to an email."""

    body: str
    """Reply body text."""


@app.post("/emails/{msg_id}/reply", summary="Reply to an email")
async def reply_email(msg_id: str, req: ReplyRequest, x_api_key: str = Header(...)):
    """Reply to an existing email. Sets correct ``In-Reply-To`` threading headers."""
    _auth(x_api_key)
    client = _client()
    thread = await client.get_thread_info(msg_id)
    subject = thread["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    return smtp_send(
        from_addr=EMAIL, app_password=APP_PASSWORD,
        to=[thread["reply_to"]], subject=subject, body=req.body,
        region=REGION, in_reply_to=thread["message_id"],
    )
