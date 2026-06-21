# REST API

`zohomail-free` ships with a self-hostable FastAPI server. Start it with:

```bash
zohomail-api
# or
uvicorn zohomail.api:app --host 0.0.0.0 --port 8000
```

Interactive docs are available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## Authentication

All endpoints (except `/health`) require an `X-API-Key` header:

```bash
curl -H "X-API-Key: your_key" http://localhost:8000/emails
```

Set `API_KEY` in your `.env` file.

---

## Endpoints

### GET /health

Liveness check. No auth required.

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

### GET /emails

List inbox messages.

**Query params:**

| Param | Default | Max | Description |
|---|---|---|---|
| `limit` | `10` | `50` | Number of messages |

```bash
curl -H "X-API-Key: your_key" \
  "http://localhost:8000/emails?limit=5"
```

```json
[
  {
    "id": "1782000221530004400",
    "from": "noreply@zohoaccounts.eu",
    "subject": "Password changed for your Zoho account",
    "time_ms": 1782000221511,
    "unread": true
  }
]
```

---

### GET /emails/{id}

Read full email by message ID.

```bash
curl -H "X-API-Key: your_key" \
  http://localhost:8000/emails/1782000221530004400
```

```json
{
  "id": "1782000221530004400",
  "from": "noreply@zohoaccounts.eu",
  "reply_to": "noreply@zohoaccounts.eu",
  "to": "you@yourdomain.com",
  "date": "Sun, 21 Jun 2026 04:03:37 +0400",
  "subject": "Password changed for your Zoho account",
  "message_id": "<abc123@eumail.zohoaccounts.com>",
  "body": "Hi, your password was changed...",
  "body_html": "<html>...</html>"
}
```

---

### POST /emails/send

Send a new email.

```bash
curl -X POST http://localhost:8000/emails/send \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["friend@example.com"],
    "subject": "Hello",
    "body": "Hi there!"
  }'
```

**Body schema:**

| Field | Type | Required | Description |
|---|---|---|---|
| `to` | `string[]` | yes | Recipients |
| `subject` | `string` | yes | Subject |
| `body` | `string` | yes | Body text or HTML |
| `cc` | `string[]` | no | CC addresses |
| `html` | `boolean` | no | Send as HTML |

---

### POST /emails/{id}/reply

Reply to an email. Sets `In-Reply-To` and `References` automatically.

```bash
curl -X POST http://localhost:8000/emails/1782000221530004400/reply \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"body": "Thanks!"}'
```

---

## Docker

```bash
docker build -t zohomail-free .
docker run -p 8000:8000 --env-file .env zohomail-free
```

## Railway

See [Getting Started](getting-started.md) for Railway deployment steps.

---

> Built by [MelkonTech](https://melkon.tech)
