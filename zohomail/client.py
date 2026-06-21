"""
Core Zoho Mail client — uses Playwright to authenticate and hit Zoho's
internal API from within the browser context (works on free-tier accounts
where IMAP/POP3 are locked behind paid plans).
"""

import json
import os
import pickle
import time
from html.parser import HTMLParser
from pathlib import Path

from playwright.async_api import async_playwright

SESSION_FILE = Path.home() / ".zohomail_session.pkl"


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)

    def get_text(self):
        return " ".join(self.parts).strip()


def strip_html(html: str) -> str:
    p = _HTMLStripper()
    p.feed(html)
    return p.get_text()


class ZohoMailClient:
    def __init__(self, email: str, password: str, region: str = "eu",
                 account_id: str = "", folder_id: str = "",
                 session_file: Path | None = None):
        self.email = email
        self.password = password
        self.region = region.lower()
        self.account_id = account_id
        self.folder_id = folder_id
        self.session_file = session_file or SESSION_FILE
        self._ml_host = f"eu1-ofzm.zoho.{'eu' if self.region == 'eu' else 'com'}"

    @property
    def _mail_url(self):
        return f"https://mail.zoho.{'eu' if self.region == 'eu' else 'com'}"

    @property
    def _accounts_url(self):
        return f"https://accounts.zoho.{'eu' if self.region == 'eu' else 'com'}"

    # ── internal ──────────────────────────────────────────────────────────────

    async def _make_context(self, p):
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        if self.session_file.exists():
            cookies = pickle.loads(self.session_file.read_bytes())
            await ctx.add_cookies(cookies)
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
        cookies = await ctx.cookies()
        self.session_file.write_bytes(pickle.dumps(cookies))

    async def _get_page(self, p):
        browser, ctx = await self._make_context(p)
        page = await ctx.new_page()

        # set up listener BEFORE navigation so we capture ml.do on page load
        self._inbox_data = None

        async def on_response(res):
            if "ml.do" in res.url:
                from urllib.parse import urlparse, parse_qs
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
            await self._login(page, ctx)
            await page.goto(f"{self._mail_url}/mail", wait_until="domcontentloaded")
            await page.wait_for_timeout(6000)

        return browser, page

    async def _discover_ids(self, page):
        """No-op — IDs are captured during _get_page navigation."""
        pass

    async def _fetch(self, page, url, params):
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        full = f"{url}?{qs}"
        result = await page.evaluate(f"""async () => {{
            const r = await fetch({json.dumps(full)}, {{credentials: 'include'}});
            return await r.text();
        }}""")
        return json.loads(result)

    # ── public API ────────────────────────────────────────────────────────────

    async def list_emails(self, limit: int = 10) -> list[dict]:
        async with async_playwright() as p:
            browser, page = await self._get_page(p)
            try:
                # reuse data already captured during page load if available
                if self._inbox_data:
                    data = self._inbox_data
                else:
                    data = await self._fetch(page, f"https://{self._ml_host}/zm/ml.do", {
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
        async with async_playwright() as p:
            browser, page = await self._get_page(p)
            try:
                await self._discover_ids(page)
                list_data = await self._fetch(page, f"https://{self._ml_host}/zm/ml.do", {
                    "xhr": int(time.time() * 1000), "mode": "listing",
                    "accId": self.account_id, "from": 1, "to": 50,
                    "summary": "true", "sortBy": "date", "sortOrder": "false",
                    "folderSpec": 2, "folId": self.folder_id,
                })
                mail_id = next(
                    (m.get("MAILID", "") for m in list_data[1]
                     if isinstance(m, dict) and m.get("M") == msg_id),
                    ""
                )
                data = await self._fetch(page, f"https://{self._ml_host}/zm/md.do", {
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
        """Return just the fields needed to reply (fast path)."""
        email = await self.read_email(msg_id)
        return {
            "reply_to":   email["reply_to"],
            "subject":    email["subject"],
            "message_id": email["message_id"],
        }
