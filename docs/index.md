# zohomail-free

**Zoho Mail for free-tier accounts — no IMAP or POP3 needed.**

Zoho locks IMAP/POP3 access behind paid plans. `zohomail-free` bypasses this by authenticating via the Zoho web UI and communicating with Zoho's internal JSON API directly — giving you full programmatic access at no cost.

---

## Features

- **Read inbox** — list and read full emails including HTML body
- **Send & reply** — compose new emails and reply with correct threading headers
- **CLI** — `zohomail list`, `zohomail read`, `zohomail send`, `zohomail reply`
- **Python library** — async `ZohoMailClient` for use in your own code
- **Self-hosted REST API** — FastAPI server, Dockerised, Railway-ready
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

---

> Built by [MelkonTech](https://melkon.tech/Melkon.Tech/ai/) · [GitHub](https://github.com/MelkonTech/zohomail-free) · [PyPI](https://pypi.org/project/zohomail-free/)
