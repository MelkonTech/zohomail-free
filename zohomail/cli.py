"""CLI entry point — installed as `zohomail` command."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path.cwd() / ".env", override=True)

from zohomail.client import ZohoMailClient
from zohomail.smtp import send as smtp_send


def _client() -> ZohoMailClient:
    email = os.environ.get("ZOHO_EMAIL")
    password = os.environ.get("ZOHO_PASSWORD")
    region = os.environ.get("ZOHO_REGION", "eu")
    if not email or not password:
        sys.exit("ERROR: set ZOHO_EMAIL and ZOHO_PASSWORD (in env or .env file)")
    return ZohoMailClient(email=email, password=password, region=region)


def _smtp_password() -> str:
    # Use ZOHO_APP_PASSWORD if set (required when 2FA is enabled),
    # otherwise fall back to the regular login password.
    pw = os.environ.get("ZOHO_APP_PASSWORD") or os.environ.get("ZOHO_PASSWORD")
    if not pw:
        sys.exit("ERROR: set ZOHO_PASSWORD (or ZOHO_APP_PASSWORD if 2FA is enabled)")
    return pw


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_list(args):
    client = _client()
    msgs = asyncio.run(client.list_emails(limit=args.limit))
    if args.json:
        print(json.dumps(msgs, indent=2))
        return
    print(f"Inbox — {len(msgs)} messages:\n")
    for m in msgs:
        flag = "*" if m["unread"] else " "
        print(f"[{flag}] {m['id']}")
        print(f"     From:    {m['from']}")
        print(f"     Subject: {m['subject']}")
        print()


def cmd_read(args):
    client = _client()
    m = asyncio.run(client.read_email(args.id))
    if args.json:
        print(json.dumps(m, indent=2))
        return
    print(f"From:       {m['from']}")
    print(f"Reply-To:   {m['reply_to']}")
    print(f"To:         {m['to']}")
    print(f"Date:       {m['date']}")
    print(f"Subject:    {m['subject']}")
    print(f"Message-ID: {m['message_id']}")
    print(f"\n{'-'*60}\n")
    print(m["body"][:4000] or "(empty)")


def cmd_send(args):
    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        sys.exit("ERROR: provide --body or --body-file")
    result = smtp_send(
        from_addr=os.environ.get("ZOHO_EMAIL", ""),
        app_password=_smtp_password(),
        to=args.to,
        subject=args.subject or "",
        body=body,
        region=os.environ.get("ZOHO_REGION", "eu"),
        cc=args.cc or [],
        html=args.html,
    )
    print(json.dumps(result))


def cmd_reply(args):
    client = _client()
    thread = asyncio.run(client.get_thread_info(args.id))
    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        sys.exit("ERROR: provide --body or --body-file")
    subject = thread["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    result = smtp_send(
        from_addr=os.environ.get("ZOHO_EMAIL", ""),
        app_password=_smtp_password(),
        to=[thread["reply_to"]],
        subject=subject,
        body=body,
        region=os.environ.get("ZOHO_REGION", "eu"),
        in_reply_to=thread["message_id"],
    )
    print(json.dumps(result))


# ── parser ────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="zohomail",
        description="Zoho Mail CLI for free-tier accounts — no IMAP needed.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list", help="list inbox messages")
    sp.add_argument("--limit", type=int, default=10)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("read", help="read a message by id")
    sp.add_argument("--id", required=True)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_read)

    sp = sub.add_parser("send", help="send a new email")
    sp.add_argument("--to", action="append", required=True)
    sp.add_argument("--cc", action="append")
    sp.add_argument("--subject")
    sp.add_argument("--body")
    sp.add_argument("--body-file")
    sp.add_argument("--html", action="store_true")
    sp.set_defaults(func=cmd_send)

    sp = sub.add_parser("reply", help="reply to an email by id")
    sp.add_argument("--id", required=True)
    sp.add_argument("--body")
    sp.add_argument("--body-file")
    sp.set_defaults(func=cmd_reply)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
