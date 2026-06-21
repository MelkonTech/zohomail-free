# Changelog

## 0.1.1 — 2026-06-21

- Clearer package description emphasising read + send + reply capabilities

## 0.1.0 — 2026-06-21

Initial release.

- `ZohoMailClient` — async client for listing and reading Zoho Mail on free-tier accounts
- `send()` — SMTP sender with HTML, CC, BCC, and reply threading support
- CLI — `zohomail list / read / send / reply`
- FastAPI REST server — `zohomail-api` with API key auth
- Docker + Railway support
- Auto session caching and re-authentication on expiry

---

> Built by [MelkonTech](https://melkon.tech/Melkon.Tech/ai/)
