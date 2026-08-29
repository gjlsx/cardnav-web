---
scope: cardnav-web
updated_at: 2026-08-29 22:53 Asia/Hong_Kong
timezone: Asia/Hong_Kong
tags: [collection, crawlee, playwright, taskexec]
summary: Root agent rules now include complete tasklist-execution checks; PriceAI browser collection is migrated into a dedicated active tasklist and is being executed.
---

# Current Status

## Confirmed architecture

- The collection path is raw-first: approved public source -> `collection_raw_payloads` / `collection_raw_records` -> explicit, local singleton merge/import worker -> existing runtime tables and public snapshots.
- New adapters use Crawlee for Python with Playwright browser collection. The new program is not implemented yet; existing collector files remain legacy and are not to be deleted.
- The original `t08292213.p038` is retained as a cancelled migration record. Its complete implementation is now the dedicated `taskexec/cardnav-web/tasklist08292253.md`, tasks `t08292253.p001`–`p005`, which collect the public PriceAI card-subscription, official-API/Token-Plan, and transit-API pages into local MySQL then explicitly merge valid records.

## Verified local entry points

- Website: `http://127.0.0.1:3101/`; verify its actual managed state with `pnpm exec astro dev status` before browser work.
- Collection control surface: `python scripts/collection/gui.py`.
- MySQL default: `127.0.0.1:3306`, database `ailovemoney`; use repository-root `.env` `MYSQL_*` values only and never record them.

## Latest verification

- `python -m unittest discover -s scripts/collection/tests` passed: 55 tests, 2026-08-29.
- Root `AGENTS.md` was compared against the user-named Likeshop and LoveMoney rules. It now includes project-specific raw-first, CLI, Astro verification, local endpoint, and sensitive-data boundaries.

## Constraints and open work

- No Crawlee/Playwright collector, approved live source configuration, source parser, persistent MySQL store, or independent worker implementation exists yet.
- Real source collection remains local, manual, exact-allowlist-only, and must not follow downstream merchant links or bypass robots, login, CAPTCHA, or challenge pages.
- Existing user edits in `README.en.md` and `README.ru.md` are uncommitted and must remain untouched.

## Next TODO

Execute every runnable `codex` task in `taskexec/cardnav-web/tasklist08292253.md`: standalone Crawlee + Playwright package, source registry, parser module, MySQL persistence facade with configurable idle reuse, CLI, fixtures, MySQL integration tests, and explicit local PriceAI raw-to-runtime verification.
