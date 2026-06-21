# zohomail-free

**Read, send, and reply to Zoho Mail emails from Python or the CLI — on a free account.**

Zoho locks IMAP/POP3 access behind paid plans, which means standard email libraries like `imaplib` simply don't work on free accounts. `zohomail-free` solves this by authenticating via the Zoho web UI and talking to their internal JSON API directly — so you can read your inbox, send emails, and reply with proper threading, all without upgrading your plan.

---

## Features

- **Read inbox** — list and read full emails including HTML body
- **Send & reply** — compose new emails and reply with correct threading headers
- **CLI** — `zohomail list`, `zohomail read`, `zohomail send`, `zohomail reply`
- **Python library** — async `ZohoMailClient` for use in your own code
- **AI integration** — `zohomail.ai` helpers to pipe emails into OpenAI, Anthropic, or any LLM
- **Session caching** — authenticates once, reuses cookie; auto re-logins on expiry

## Install

```bash
pip install zohomail-free
playwright install chromium
```

## Quick example

```python
import asyncio
from zohomail import ZohoMailClient

client = ZohoMailClient(
    email="you@yourdomain.com",
    password="your_password",
    region="eu",
)

emails = asyncio.run(client.list_emails(limit=5))
for e in emails:
    print(e["subject"], "—", e["from"])
```

## CLI

```bash
zohomail list
zohomail read --id 1782000221530004400
zohomail send --to friend@example.com --subject "Hi" --body "Hello!"
zohomail reply --id 1782000221530004400 --body "Thanks!"
```

## REST API

Don't want to install anything? Use the hosted REST API at **[zohomail.free.melkon.tech](https://zohomail.free.melkon.tech)**:

```bash
curl https://zohomail.free.melkon.tech/emails \
  -H "x-zoho-email: you@yourdomain.com" \
  -H "x-zoho-password: yourpassword" \
  -H "x-zoho-region: eu"
```

Interactive docs at **[zohomail.free.melkon.tech/docs](https://zohomail.free.melkon.tech/docs)** — no sign-up, no API key, just your Zoho credentials.

---

> Built by [MelkonTech](https://melkon.tech) · [GitHub](https://github.com/MelkonTech/zohomail-free) · [PyPI](https://pypi.org/project/zohomail-free/)
