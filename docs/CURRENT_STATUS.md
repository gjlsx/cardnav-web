---
scope: cardnav-web
updated_at: 2026-08-30 04:25 Asia/Hong_Kong
timezone: Asia/Hong_Kong
tags: [collection, crawlee, playwright, taskexec]
summary: PriceAI Crawlee CLI exists; collect/merge programs stay hardcoded and share scripts/crawlee_collection/catch.config for source set, recrawl sleep, and merge intervals.
---

# Current Status

## Confirmed architecture

- The collection path is raw-first: approved public source -> `collection_raw_payloads` / `collection_raw_records` -> explicit, local singleton merge/import worker -> existing runtime tables and public snapshots. Table roles are listed in `docs/数据库说明.md`.
- New adapters use Crawlee for Python with PlaywrightCrawler. The independent program lives in `scripts/crawlee_collection/`. Existing `scripts/collection/` files remain legacy and must not be called from the new CLI or worker.
- Collect/parse/merge programs and order are hardcoded. Source subset, item caps, recrawl sleep, and merge-worker intervals belong in one `scripts/crawlee_collection/catch.config` (see `catch.config.example`). Every CLI subcommand, future GUI button, and Linux one-shot must read that file through the same CLI. Config cannot add URLs outside the code allowlist.
- The original `t08292213.p038` remains a cancelled migration record. Implementation is `taskexec/cardnav-web/tasklist08292253.md` tasks `t08292253.p001`–`p005`.

## Verified local entry points

- Website: `http://127.0.0.1:3101/`; verify its actual managed state with `pnpm exec astro dev status` before browser work.
- Legacy collection GUI: `python scripts/collection/gui.py`.
- New collector CLI: `python -m scripts.crawlee_collection check-config`.
- New collector GUI: `python -m scripts.crawlee_collection.gui` (collect tab and merge tab; buttons call the CLI).
- MySQL default: `127.0.0.1:3306`, database `ailovemoney`; use repository-root `.env` `MYSQL_*` values only and never record them.

## Latest verification

- Crawlee unit tests 20 passed; legacy `python -m unittest discover -s scripts/collection/tests` 55 passed, 2026-08-29.
- Local PriceAI collect `--all` wrote batch `batch-20260829153013-239622` (67 valid raw records) and merge-once imported 67 runtime rows. Transit raw payload was stored with 0 parsed gateway rows because the public listing JSON has no site homepage.

## Constraints and open work

- Real source collection remains local, manual, exact-allowlist-only, and must not follow downstream merchant links or bypass robots, login, CAPTCHA, or challenge pages.
- This site does not support Russian. `README.ru.md` is deleted and must not be restored; public READMEs are Chinese and English only.
- `tasklist08281547.md` is archived in the index only (`docs/backuptask/`); its task rows were not rewritten. Current execute list is `tasklist08292253.md`.

## Next TODO

No runnable `todo` remains in `taskexec/cardnav-web/tasklist08292253.md`. Optional later: map PriceAI transit ranking rows if a public site homepage field appears, without following downstream links. GUI/Linux continue to call `python -m scripts.crawlee_collection` / `python -m scripts.crawlee_collection.gui`.
