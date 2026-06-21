# zohomail-free

[![PyPI version](https://img.shields.io/pypi/v/zohomail-free.svg)](https://pypi.org/project/zohomail-free/)
[![Python 3.11+](https://img.shields.io/pypi/pyversions/zohomail-free.svg)](https://pypi.org/project/zohomail-free/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Built by [MelkonTech](https://melkon.tech)  
> [Documentation](https://melkontech.github.io/zohomail-free/) · [PyPI](https://pypi.org/project/zohomail-free/) · [GitHub](https://github.com/MelkonTech/zohomail-free)

**Read, send, and reply to Zoho Mail emails from Python or the CLI — on a free account.**

Zoho locks IMAP/POP3 behind paid plans, so standard email libraries don't work on free accounts. `zohomail-free` works around this by authenticating via the Zoho web UI and calling their internal API directly — giving you full inbox access and SMTP sending without paying for a plan.

## Install

```bash
pip install zohomail-free
playwright install chromium
```

## Setup

Create a `.env` file with your credentials:

```env
ZOHO_EMAIL=you@yourdomain.com
ZOHO_PASSWORD=your_zoho_login_password
ZOHO_REGION=eu   # eu or com

# Optional — only needed if you have 2FA enabled on your Zoho account.
# If not set, ZOHO_PASSWORD is used for SMTP sending instead.
ZOHO_APP_PASSWORD=your_app_specific_password
```

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
    to=["friend@example.com"],
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

## AI integration

Helpers in `zohomail.ai` make it easy to pipe emails into any LLM without extra dependencies:

```python
import asyncio
from openai import OpenAI
from zohomail import ZohoMailClient
from zohomail.ai import emails_to_messages, email_to_prompt

client = ZohoMailClient(email="you@zoho.com", password="...", region="eu")
emails = asyncio.run(client.list_emails(limit=10))

# Summarise inbox with OpenAI
oai = OpenAI()
resp = oai.chat.completions.create(
    model="gpt-4o-mini",
    messages=emails_to_messages(emails, system="Summarise these emails briefly."),
)
print(resp.choices[0].message.content)

# Draft a reply with Claude
import anthropic
email = asyncio.run(client.read_email(emails[0]["id"]))

ac = anthropic.Anthropic()
msg = ac.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[{"role": "user", "content": email_to_prompt(email, "Write a short reply:")}],
)
print(msg.content[0].text)
```

Available helpers: `email_to_text`, `email_to_prompt`, `emails_to_messages`, `email_to_tool_result`.

## Hosted REST API

Don't want to install anything? Use the free hosted API at **[zohomail.free.melkon.tech](https://zohomail.free.melkon.tech)**:

```bash
curl https://zohomail.free.melkon.tech/emails \
  -H "x-zoho-email: you@yourdomain.com" \
  -H "x-zoho-password: yourpassword" \
  -H "x-zoho-region: eu"
```

Interactive docs at **[zohomail.free.melkon.tech/docs](https://zohomail.free.melkon.tech/docs)** — no sign-up, no API key.

## How it works

Zoho's free plan blocks IMAP/POP3 with `ACCESS_RESTRICTED_BY_ZOHOMAIL`. However, their web UI talks to an internal JSON API (`ml.do` / `md.do`) over HTTPS. This library uses Playwright to authenticate once, saves the session cookie at `~/.zohomail_session.pkl`, then makes API calls from within the browser context — no paid plan needed.

On subsequent runs the saved session is reused. If it expires, the library re-authenticates automatically.

## Documentation

Full docs at **[melkontech.github.io/zohomail-free](https://melkontech.github.io/zohomail-free/)**

## Author

Built by [MelkonTech](https://melkon.tech)

## License

MIT — see [LICENSE](LICENSE)
