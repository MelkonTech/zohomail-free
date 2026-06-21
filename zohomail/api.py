"""FastAPI server — self-hostable REST API for Zoho Mail."""

import json
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
    description="Zoho Mail REST API for free-tier accounts. No IMAP needed.",
    version="0.1.0",
)


def _auth(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _client() -> ZohoMailClient:
    return ZohoMailClient(email=EMAIL, password=PASSWORD, region=REGION)


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/emails")
async def list_emails(limit: int = Query(10, le=50), x_api_key: str = Header(...)):
    _auth(x_api_key)
    return await _client().list_emails(limit=limit)


@app.get("/emails/{msg_id}")
async def read_email(msg_id: str, x_api_key: str = Header(...)):
    _auth(x_api_key)
    return await _client().read_email(msg_id)


class SendRequest(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: list[str] = []
    html: bool = False


@app.post("/emails/send")
async def send_email(req: SendRequest, x_api_key: str = Header(...)):
    _auth(x_api_key)
    return smtp_send(
        from_addr=EMAIL, app_password=APP_PASSWORD,
        to=req.to, subject=req.subject, body=req.body,
        region=REGION, cc=req.cc, html=req.html,
    )


class ReplyRequest(BaseModel):
    body: str


@app.post("/emails/{msg_id}/reply")
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
