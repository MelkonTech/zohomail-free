# Changelog

All notable changes to `zohomail-free` are documented here.

## 1.0.0 - 2026-07-24

First stable release.

### Added
- **Attachments** — `read_email()` now returns an `attachments` list. Each entry
  has `name`, `format`, `size_bytes`, `part_id`, `attachment_id`, and `inline`,
  parsed from Zoho's `NEWATT` metadata (previously discarded).
- **MCP integration** — the hosted API exposes a Model Context Protocol endpoint
  (`/mcp`) so Zoho Mail can plug directly into Claude, Cursor, or any
  MCP-compatible assistant. Tools: `list_emails`, `read_email`, `send_email`,
  `reply_email`. See the README for config.
- **Type marker** — ships `py.typed` (PEP 561), so downstream type checkers now
  pick up the library's type hints.
- **Test suite** — pytest coverage for HTML stripping, attachment parsing, SMTP
  message construction, and the AI helpers; runs with no Zoho account or network.
- **CI** — GitHub Actions runs the tests on Python 3.11/3.12/3.13, and a
  Trusted-Publishing workflow releases to PyPI on each GitHub Release.

### Changed
- **More reliable auth on servers.** Chromium launches with a serverless-hardened
  flag set (`--no-sandbox`, `--single-process`, `--no-zygote`,
  swiftshader GL, and more) so it runs inside Docker, AWS Lambda, and CI.
- **More robust login and inbox load.** Login cycles through Zoho's consent
  prompts, and the inbox load waits for the `ml.do` API response instead of a
  fixed sleep — fewer flaky "could not discover API host" failures.

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
