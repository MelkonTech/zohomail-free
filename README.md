# zohomail-free

[![PyPI version](https://img.shields.io/pypi/v/zohomail-free.svg)](https://pypi.org/project/zohomail-free/)
[![Python 3.11+](https://img.shields.io/pypi/pyversions/zohomail-free.svg)](https://pypi.org/project/zohomail-free/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Built by [MelkonTech](https://melkon.tech)  
> [Documentation](https://melkontech.github.io/zohomail-free/) · [PyPI](https://pypi.org/project/zohomail-free/) · [GitHub](https://github.com/MelkonTech/zohomail-free)

**Read, send, and reply to Zoho Mail emails from Python or the command line — on a free account.**

Zoho locks IMAP/POP3 behind paid plans, so standard email libraries don't work on free accounts. `zohomail-free` works around this by authenticating via the Zoho web UI and calling their internal API directly — giving you full inbox access and SMTP sending without paying for a plan.

## Install

```bash
pip install zohomail-free
playwright install chromium
```

## Setup

Create a `.env` file with your credentials:

```bash
ZOHO_EMAIL=you@yourdomain.com
ZOHO_PASSWORD=your_zoho_login_password
ZOHO_APP_PASSWORD=your_app_specific_password   # for sending
ZOHO_REGION=eu   # eu or com
```

> Generate an app-specific password in Zoho Mail → Settings → Security → App Passwords.

## Python

```python
import asyncio
from zohomail import ZohoMailClient, send

client = ZohoMailClient(
    email="you@yourdomain.com",
    password="your_password",
    region="eu",
)

# List inbox
emails = asyncio.run(client.list_emails(limit=5))
for e in emails:
    print(e["subject"], "—", e["from"])

# Read a full email
email = asyncio.run(client.read_email(emails[0]["id"]))
print(email["body"])

# Send an email
send(
    from_addr="you@yourdomain.com",
    app_password="your_app_password",
    to="friend@example.com",
    subject="Hello",
    body="Hi there!",
    region="eu",
)
```

## CLI

```bash
# List inbox
zohomail list
zohomail list --limit 20 --json

# Read a message (get the id from list output)
zohomail read --id 1782000221530004400

# Send a new email
zohomail send --to someone@example.com --subject "Hello" --body "Hi there"

# Reply to an email (preserves threading)
zohomail reply --id 1782000221530004400 --body "Thanks!"
```

## Self-hosted REST API

Run a local API server over your Zoho account:

```bash
# Set API_KEY in your .env, then:
zohomail-api

# Or with Docker
docker build -t zohomail-free .
docker run -p 8000:8000 --env-file .env zohomail-free
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/emails` | List inbox (`?limit=10`) |
| GET | `/emails/{id}` | Read full email |
| POST | `/emails/send` | Send new email |
| POST | `/emails/{id}/reply` | Reply to email |
| GET | `/health` | Health check |

All endpoints require `X-API-Key: <your_key>` header.

```bash
curl -H "X-API-Key: your_key" http://localhost:8000/emails
```

## How it works

Zoho's free plan blocks IMAP/POP3 with `ACCESS_RESTRICTED_BY_ZOHOMAIL`. However, their web UI talks to an internal JSON API (`ml.do` / `md.do`) over HTTPS. This library uses Playwright to authenticate once, saves the session cookie at `~/.zohomail_session.pkl`, then makes API calls from within the browser context where cookies are correctly scoped — no paid plan needed.

On subsequent runs the saved session is reused. If it expires, the library re-authenticates automatically.

## Documentation

Full docs at **[melkontech.github.io/zohomail-free](https://melkontech.github.io/zohomail-free/)**

## Author

Built by [MelkonTech](https://melkon.tech)

## License

MIT — see [LICENSE](LICENSE)
