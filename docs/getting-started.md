# Getting Started

## Requirements

- Python 3.11+
- A Zoho Mail account (free tier works)
- An app-specific password (see below)

## Installation

```bash
pip install zohomail-free
playwright install chromium
```

## Credentials

You need three things:

| Variable | Description |
|---|---|
| `ZOHO_EMAIL` | Your Zoho address, e.g. `you@yourdomain.com` |
| `ZOHO_PASSWORD` | Your Zoho **login** password |
| `ZOHO_APP_PASSWORD` | An **app-specific** password for SMTP sending |
| `ZOHO_REGION` | `eu` or `com` depending on where your account is hosted |

### Generate an app-specific password

1. Log into Zoho Mail
2. Go to **Settings → Security → App Passwords**
3. Click **Generate New Password**, name it anything (e.g. `zohomail-free`)
4. Copy the generated password — you won't see it again

!!! note
    Your regular login password works for reading (via the browser session),
    but Zoho requires an app-specific password for SMTP sending.

## Configuration

Create a `.env` file in your project directory:

```bash
cp .env.example .env
```

```ini title=".env"
ZOHO_EMAIL=you@yourdomain.com
ZOHO_PASSWORD=your_login_password
ZOHO_APP_PASSWORD=your_app_specific_password
ZOHO_REGION=eu
API_KEY=changeme   # only needed for the REST API server
```

## First run

```bash
zohomail list
```

On first run, Playwright opens a headless browser, logs in, and saves the session to `~/.zohomail_session.pkl`. Subsequent calls reuse the cookie — no browser startup needed until the session expires (~30 days).

---

> Built by [MelkonTech](https://melkon.tech)
