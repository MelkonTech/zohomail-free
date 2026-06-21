# CLI Reference

The `zohomail` command is installed automatically with the package.

## list

List inbox messages, newest first.

```bash
zohomail list [--limit N] [--json]
```

| Flag | Default | Description |
|---|---|---|
| `--limit` | `10` | Number of messages to show |
| `--json` | off | Output raw JSON |

**Example:**

```bash
zohomail list --limit 5
```

```
Inbox — 3 messages:

[*] 1782000221530004400
     From:    noreply@zohoaccounts.eu
     Subject: Password changed for your Zoho account

[ ] 1781999832376005600
     From:    friend@example.com
     Subject: Re: Hello
```

`[*]` = unread, `[ ]` = read.

---

## read

Read the full content of a message by its ID.

```bash
zohomail read --id <message_id> [--json]
```

| Flag | Required | Description |
|---|---|---|
| `--id` | yes | Message ID from `zohomail list` output |
| `--json` | no | Output raw JSON including HTML body |

**Example:**

```bash
zohomail read --id 1782000221530004400
```

---

## send

Send a new email.

```bash
zohomail send --to <addr> [--to <addr>] --subject "..." --body "..." [--cc <addr>] [--html] [--body-file path]
```

| Flag | Required | Description |
|---|---|---|
| `--to` | yes | Recipient (repeat for multiple) |
| `--subject` | no | Subject line |
| `--body` | no* | Message body |
| `--body-file` | no* | Read body from a file |
| `--cc` | no | CC address (repeatable) |
| `--html` | no | Send body as HTML |

*One of `--body` or `--body-file` is required.

**Example:**

```bash
zohomail send \
  --to friend@example.com \
  --subject "Hello from zohomail-free" \
  --body "Hi! This was sent via zohomail-free."
```

---

## reply

Reply to an existing email. Threading headers (`In-Reply-To`, `References`) are set automatically.

```bash
zohomail reply --id <message_id> --body "..." [--body-file path]
```

**Example:**

```bash
zohomail reply --id 1782000221530004400 --body "Thanks, got it!"
```

---

> Built by [MelkonTech](https://melkon.tech/Melkon.Tech/ai/)
