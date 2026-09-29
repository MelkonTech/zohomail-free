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
    msgs = asyncio.run(client.list_emails(limit=args.limit, folder=args.folder,
                                          conversations=args.conversations))
    if args.json:
        print(json.dumps(msgs, indent=2))
        return
    print(f"{args.folder or 'Inbox'}: {len(msgs)} messages\n")
    for m in msgs:
        flag = "*" if m["unread"] else " "
        print(f"[{flag}] {m['id']}")
        print(f"     From:    {m['from']}")
        if m.get("to"):
            print(f"     To:      {m['to']}")
        print(f"     Subject: {m['subject']}")
        print()


def cmd_read(args):
    client = _client()
    m = asyncio.run(client.read_email(args.id, folder=args.folder))
    if args.json:
        print(json.dumps(m, indent=2))
        return
    print(f"From:       {m['from']}")
    print(f"Reply-To:   {m['reply_to']}")
    print(f"To:         {m['to']}")
    print(f"Date:       {m['date']}")
    print(f"Subject:    {m['subject']}")
    print(f"Message-ID: {m['message_id']}")
    atts = m.get("attachments") or []
    if atts:
        print("Attachments:")
        for a in atts:
            tag = " (inline)" if a["inline"] else ""
            print(f"  {a['name']}  {a['size_bytes']} bytes{tag}")
    print(f"\n{'-'*60}\n")
    print(m["body"] or "(empty)")


def cmd_download(args):
    client = _client()
    paths = asyncio.run(client.download_attachments(
        args.id, args.out, folder=args.folder, include_inline=args.inline))
    if not paths:
        print("No attachments to download.")
        return
    for p in paths:
        print(f"{p}  {p.stat().st_size} bytes")


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
    sp.add_argument("--folder", default=None, help='folder name, e.g. Sent, Drafts, Spam (default Inbox)')
    sp.add_argument("--conversations", action="store_true",
                    help="group into threads like the web UI (hides own replies inside a thread)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("read", help="read a message by id")
    sp.add_argument("--id", required=True)
    sp.add_argument("--folder", default=None, help="folder the id lives in (default Inbox)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_read)

    sp = sub.add_parser("download", help="download a message's attachments")
    sp.add_argument("--id", required=True)
    sp.add_argument("--folder", default=None, help="folder the id lives in (default Inbox)")
    sp.add_argument("--out", default=".", help="destination directory (default current dir)")
    sp.add_argument("--inline", action="store_true", help="also download inline images")
    sp.set_defaults(func=cmd_download)

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
