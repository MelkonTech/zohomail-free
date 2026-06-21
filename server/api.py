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
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

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
        "Built by [MelkonTech](https://melkon.tech)"
    ),
    version="0.1.0",
    contact={
        "name": "MelkonTech",
        "url": "https://melkon.tech",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/MelkonTech/zohomail-free/blob/main/LICENSE",
    },
)


def _auth(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _client() -> ZohoMailClient:
    return ZohoMailClient(email=EMAIL, password=PASSWORD, region=REGION)


@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok"}


@app.get("/emails", summary="List inbox messages")
async def list_emails(
    limit: int = Query(10, le=50, description="Number of messages to return"),
    x_api_key: str = Header(...),
):
    _auth(x_api_key)
    return await _client().list_emails(limit=limit)


@app.get("/emails/{msg_id}", summary="Read a full email")
async def read_email(msg_id: str, x_api_key: str = Header(...)):
    _auth(x_api_key)
    return await _client().read_email(msg_id)


class SendRequest(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: list[str] = []
    html: bool = False


@app.post("/emails/send", summary="Send a new email")
async def send_email(req: SendRequest, x_api_key: str = Header(...)):
    _auth(x_api_key)
    return smtp_send(
        from_addr=EMAIL, app_password=APP_PASSWORD,
        to=req.to, subject=req.subject, body=req.body,
        region=REGION, cc=req.cc, html=req.html,
    )


class ReplyRequest(BaseModel):
    body: str


@app.post("/emails/{msg_id}/reply", summary="Reply to an email")
async def reply_email(msg_id: str, req: ReplyRequest, x_api_key: str = Header(...)):
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
