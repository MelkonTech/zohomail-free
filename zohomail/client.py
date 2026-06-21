"""
Core Zoho Mail client.

Uses Playwright to authenticate and hit Zoho's internal API from within
the browser context. Works on free-tier accounts where IMAP/POP3 are
locked behind paid plans.

Example:
    >>> import asyncio
    >>> from zohomail.client import ZohoMailClient
    >>> client = ZohoMailClient(email="you@example.com", password="secret")
    >>> emails = asyncio.run(client.list_emails(limit=5))
    >>> print(emails[0]["subject"])
"""

import json
import pickle
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright

import os
# Lambda only allows writes to /tmp; use it when HOME isn't writable
_default_session_dir = Path("/tmp") if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else Path.home()
SESSION_FILE = _default_session_dir / ".zohomail_session.pkl"


class ZohoMailError(Exception):
    """Base exception for all zohomail-free errors."""


class SessionExpiredError(ZohoMailError):
    """Raised when the Zoho session expires and re-authentication fails."""


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)

    def get_text(self):
        return " ".join(self.parts).strip()


def strip_html(html: str) -> str:
    """Strip HTML tags and return plain text.

    Args:
        html: Raw HTML string.

    Returns:
        Plain text with tags removed and whitespace normalised.
    """
    p = _HTMLStripper()
    p.feed(html)
    return p.get_text()


class ZohoMailClient:
    """Async Zoho Mail client for free-tier accounts.

    Authenticates via the Zoho web UI using Playwright, then communicates
    with Zoho's internal JSON API (``ml.do`` / ``md.do``). The session
    cookie is cached at ``~/.zohomail_session.pkl`` and reused on subsequent
    calls. If the session expires the client re-authenticates automatically.

    Args:
        email: Your Zoho Mail address (e.g. ``you@yourdomain.com``).
        password: Your Zoho account login password (not an app password).
        region: Zoho data-centre region — ``"eu"`` (default) or ``"com"``.
        account_id: Internal Zoho account ID. Auto-discovered if omitted.
        folder_id: Internal Zoho inbox folder ID. Auto-discovered if omitted.
        session_file: Path for the session cookie cache. Defaults to
            ``~/.zohomail_session.pkl``.

    Example:
        >>> client = ZohoMailClient(
        ...     email="you@yourdomain.com",
        ...     password="your_password",
        ...     region="eu",
        ... )
        >>> emails = asyncio.run(client.list_emails(limit=10))
    """

    def __init__(
        self,
        email: str,
        password: str,
        region: str = "eu",
        account_id: str = "",
        folder_id: str = "",
        session_file: Path | None = None,
    ):
        self.email = email
        self.password = password
        self.region = region.lower()
        self.account_id = account_id
        self.folder_id = folder_id
        self.session_file = session_file or SESSION_FILE
        self._ml_host: str = ""
        self._inbox_data = None

    @property
    def _mail_url(self) -> str:
        return f"https://mail.zoho.{'eu' if self.region == 'eu' else 'com'}"

    @property
    def _accounts_url(self) -> str:
        return f"https://accounts.zoho.{'eu' if self.region == 'eu' else 'com'}"

    # ── internal ──────────────────────────────────────────────────────────────

    async def _make_context(self, p):
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        if self.session_file.exists():
            try:
                cookies = pickle.loads(self.session_file.read_bytes())
                await ctx.add_cookies(cookies)
            except Exception:
                pass
        return browser, ctx

    async def _login(self, page, ctx):
        await page.goto(f"{self._accounts_url}/signin?servicename=ZohoMail")
        await page.wait_for_load_state("domcontentloaded")
        await page.fill("#login_id", self.email)
        await page.click("#nextbtn")
        await page.wait_for_timeout(2000)
        await page.fill("#password", self.password)
        await page.click("#nextbtn")
        await page.wait_for_timeout(4000)
        if "tfa-banner" in page.url or "announcement" in page.url:
            try:
                await page.click("text=Continue")
                await page.wait_for_timeout(2000)
            except Exception:
                pass
        if "signin" in page.url or "accounts.zoho" in page.url:
            raise ZohoMailError("Login failed — check ZOHO_EMAIL and ZOHO_PASSWORD")
        cookies = await ctx.cookies()
        self.session_file.write_bytes(pickle.dumps(cookies))

    async def _get_page(self, p):
        browser, ctx = await self._make_context(p)
        page = await ctx.new_page()
        self._inbox_data = None

        async def on_response(res):
            if "ml.do" in res.url:
                parsed = urlparse(res.url)
                qs = parse_qs(parsed.query)
                self.account_id = self.account_id or (qs.get("accId") or [""])[0]
                self.folder_id  = self.folder_id  or (qs.get("folId") or [""])[0]
                self._ml_host   = parsed.netloc
                try:
                    self._inbox_data = await res.json()
                except Exception:
                    pass

        page.on("response", on_response)
        await page.goto(f"{self._mail_url}/mail", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        if "signin" in page.url or "accounts.zoho" in page.url:
            if self.session_file.exists():
                self.session_file.unlink()
            await self._login(page, ctx)
            self._inbox_data = None
            await page.goto(f"{self._mail_url}/mail", wait_until="domcontentloaded")
            await page.wait_for_timeout(6000)

        if not self._ml_host:
            raise ZohoMailError(
                "Could not discover Zoho API host. "
                "The page may not have loaded correctly."
            )

        return browser, page

    async def _fetch(self, page, url: str, params: dict):
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        full = f"{url}?{qs}"
        result = await page.evaluate(f"""async () => {{
            const r = await fetch({json.dumps(full)}, {{credentials: 'include'}});
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return await r.text();
        }}""")
        if not result:
            raise ZohoMailError(f"Empty response from {url}")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            raise ZohoMailError(f"Unexpected response from Zoho API: {result[:200]}")

    def _ml_url(self) -> str:
        if not self._ml_host:
            raise ZohoMailError("API host not yet discovered — call list_emails first")
        return f"https://{self._ml_host}/zm/ml.do"

    def _md_url(self) -> str:
        if not self._ml_host:
            raise ZohoMailError("API host not yet discovered — call list_emails first")
        return f"https://{self._ml_host}/zm/md.do"

    # ── public API ────────────────────────────────────────────────────────────

    async def list_emails(self, limit: int = 10) -> list[dict]:
        """List the most recent inbox messages.

        Authenticates if needed, then returns a list of email summaries
        sorted newest-first. The inbox data is captured from network traffic
        during page load, so no extra API call is made.

        Args:
            limit: Maximum number of messages to return. Defaults to ``10``,
                max ``50``.

        Returns:
            A list of dicts, each containing:

            - ``id`` (*str*) — Zoho message ID, used with :meth:`read_email`.
            - ``from`` (*str*) — Sender email address.
            - ``subject`` (*str*) — Message subject.
            - ``time_ms`` (*int*) — Received timestamp in milliseconds.
            - ``unread`` (*bool*) — ``True`` if the message is unread.

        Raises:
            ZohoMailError: If authentication or the API call fails.

        Example:
            >>> emails = asyncio.run(client.list_emails(limit=5))
            >>> for e in emails:
            ...     print(e["subject"], "-", e["from"])
        """
        async with async_playwright() as p:
            browser, page = await self._get_page(p)
            try:
                if self._inbox_data:
                    data = self._inbox_data
                else:
                    data = await self._fetch(page, self._ml_url(), {
                        "xhr": int(time.time() * 1000), "mode": "listing",
                        "accId": self.account_id, "from": 1, "to": limit,
                        "summary": "true", "sortBy": "date", "sortOrder": "false",
                        "folderSpec": 2, "folId": self.folder_id,
                    })
                msgs = [m for m in data[1] if isinstance(m, dict) and "M" in m]
                return [
                    {
                        "id":      m["M"],
                        "from":    m.get("F", ""),
                        "subject": m.get("SB", ""),
                        "time_ms": int(m.get("LTIME", 0)),
                        "unread":  m.get("RS", 1) != 1,
                    }
                    for m in msgs[:limit]
                ]
            finally:
                await browser.close()

    async def read_email(self, msg_id: str) -> dict:
        """Read the full content of a single email.

        Fetches the complete message including HTML body, sender details,
        and threading headers needed for replies.

        Args:
            msg_id: The Zoho message ID (``id`` field from :meth:`list_emails`).

        Returns:
            A dict containing:

            - ``id`` (*str*) — Zoho message ID.
            - ``from`` (*str*) — Sender email address.
            - ``reply_to`` (*str*) — Address to send replies to.
            - ``to`` (*str*) — Recipient address.
            - ``date`` (*str*) — Human-readable sent date.
            - ``subject`` (*str*) — Message subject.
            - ``message_id`` (*str*) — RFC 2822 Message-ID for threading.
            - ``body`` (*str*) — Plain-text body (stripped from HTML).
            - ``body_html`` (*str*) — Raw HTML body.

        Raises:
            ZohoMailError: If authentication or the API call fails.

        Example:
            >>> email = asyncio.run(client.read_email("1782000221530004400"))
            >>> print(email["body"])
        """
        async with async_playwright() as p:
            browser, page = await self._get_page(p)
            try:
                inbox = self._inbox_data
                if not inbox:
                    inbox = await self._fetch(page, self._ml_url(), {
                        "xhr": int(time.time() * 1000), "mode": "listing",
                        "accId": self.account_id, "from": 1, "to": 50,
                        "summary": "true", "sortBy": "date", "sortOrder": "false",
                        "folderSpec": 2, "folId": self.folder_id,
                    })
                mail_id = next(
                    (m.get("MAILID", "") for m in inbox[1]
                     if isinstance(m, dict) and m.get("M") == msg_id),
                    ""
                )
                data = await self._fetch(page, self._md_url(), {
                    "xhr": int(time.time() * 1000), "accId": self.account_id,
                    "summary": "true", "msgId": msg_id, "vfc": "false",
                    "split": "true", "folId": self.folder_id, "mailId": mail_id,
                })
                md = data[1]["mdata"]
                html = md.get("CONTENT", "")
                return {
                    "id":         msg_id,
                    "from":       md.get("FROM", ""),
                    "reply_to":   md.get("REPLYTO") or md.get("FROM", ""),
                    "to":         md.get("DELIVEREDTO", ""),
                    "date":       md.get("SENTTIME", ""),
                    "subject":    md.get("SB", ""),
                    "message_id": md.get("MAILID", ""),
                    "body":       strip_html(html) if html else "",
                    "body_html":  html,
                }
            finally:
                await browser.close()

    async def get_thread_info(self, msg_id: str) -> dict:
        """Return the minimal headers needed to reply to a message.

        A lightweight alternative to :meth:`read_email` when you only need
        to send a reply and don't need the body.

        Args:
            msg_id: The Zoho message ID.

        Returns:
            A dict with ``reply_to``, ``subject``, and ``message_id`` keys.

        Raises:
            ZohoMailError: If authentication or the API call fails.
        """
        email = await self.read_email(msg_id)
        return {
            "reply_to":   email["reply_to"],
            "subject":    email["subject"],
            "message_id": email["message_id"],
        }
