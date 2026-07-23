# Changelog

All notable changes to `zohomail-free` are documented here.

## 1.0.0 - 2026-07-24

First stable release.

### Added
- **MCP integration** — the hosted API now exposes a Model Context Protocol
  endpoint (`/mcp`) so Zoho Mail can be plugged directly into Claude, Cursor, or
  any MCP-compatible assistant. Tools: `list_emails`, `read_email`, `send_email`,
  `reply_email`. See the README for config.

### Changed
- Chromium now launches with `--no-sandbox`, `--disable-dev-shm-usage`, and
  `--disable-gpu`, so the client runs reliably inside Docker, AWS Lambda, and CI
  containers.

## 0.1.5 - 2026-06-21
- Use `/tmp` for the session cache on AWS Lambda.

## 0.1.4
- `ZOHO_APP_PASSWORD` is optional; falls back to the regular password.

## 0.1.3
- Add `zohomail.ai`, move server to `server/`, slim package dependencies.

## 0.1.2
- Badges, fixed author URLs, docs URL on PyPI, cleaner README.

## 0.1.1
- Clearer description — read, send, reply on free accounts.

## 0.1.0
- Initial public release on PyPI.
