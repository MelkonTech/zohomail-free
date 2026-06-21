# zohomail-free

Zoho Mail client for **free-tier accounts** — no IMAP or POP3 needed.

Zoho locks IMAP/POP3 behind paid plans. This library authenticates via the web UI and uses Zoho's internal API directly, giving you full programmatic access for free.

## Install

```bash
# from source (PyPI release coming soon)
pip install git+https://github.com/MelkonTech/zohomail-free.git
playwright install chromium
```

## Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
ZOHO_EMAIL=you@yourdomain.com
ZOHO_PASSWORD=your_zoho_login_password
ZOHO_APP_PASSWORD=your_app_specific_password   # for sending
ZOHO_REGION=eu   # eu or com
```

> Generate an app-specific password in Zoho Mail → Settings → Security → App Passwords.

## CLI

```bash
# list inbox
zohomail list
zohomail list --limit 20 --json

# read a message (get the id from list output)
zohomail read --id 1782000221530004400

# send new email
zohomail send --to someone@example.com --subject "Hello" --body "Hi there"

# reply to an email
zohomail reply --id 1782000221530004400 --body "Thanks!"
```

## Python

```python
import asyncio
from zohomail.client import ZohoMailClient

client = ZohoMailClient(
    email="you@yourdomain.com",
    password="your_password",
    region="eu",
)

# list inbox
emails = asyncio.run(client.list_emails(limit=5))
for e in emails:
    print(e["subject"], "-", e["from"])

# read full email
email = asyncio.run(client.read_email(emails[0]["id"]))
print(email["body"])
```

## Self-hosted API

```bash
cp .env.example .env   # fill in credentials + set a strong API_KEY

# with Docker
docker build -t zohomail-free .
docker run -p 8000:8000 --env-file .env zohomail-free

# or directly
pip install git+https://github.com/MelkonTech/zohomail-free.git
zohomail-api
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/emails` | List inbox (`?limit=10`) |
| GET | `/emails/{id}` | Read full email |
| POST | `/emails/send` | Send new email |
| POST | `/emails/{id}/reply` | Reply to email |
| GET | `/health` | Health check |

All endpoints require `X-API-Key: <your_key>` header (set `API_KEY` in `.env`).

```bash
curl -H "X-API-Key: your_key" http://localhost:8000/emails
```

## Deploy to Railway

1. Fork this repo on GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Select your fork
4. Add environment variables from `.env.example` in Railway's Variables tab
5. Deploy — Railway auto-detects the Dockerfile

## How it works

Zoho's free plan blocks IMAP/POP3 with `ACCESS_RESTRICTED_BY_ZOHOMAIL`. However, their web UI communicates with an internal JSON API (`ml.do` / `md.do`) over HTTPS. This library uses Playwright to authenticate once, saves the session cookie, then makes API calls from within the browser context where cookies are correctly scoped — no paid plan required.

Session cookies are cached at `~/.zohomail_session.pkl` and reused on subsequent runs. If the session expires, the library automatically re-authenticates.

## License

MIT — see [LICENSE](LICENSE)
