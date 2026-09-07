# ai.lovemoney.live Implementation Plan

> Historical implementation plan, not active work. Delivery is recorded in [archived tasklist08280357](../../../taskexec/cardnav-web/docs/backuptask/tasklist08280357.md). Branding and current priorities are superseded by [PRODUCT_STRATEGY](../../PRODUCT_STRATEGY.md), [ROADMAP](../../ROADMAP.md) and [CURRENT_STATUS](../../CURRENT_STATUS.md). Do not rerun these steps from historical checkboxes.

**Goal:** Rebrand and simplify the public site, make MySQL its only database, and deploy it safely behind Apache on port 80.

**Architecture:** Centralize public brand/contact values in `src/site.ts`; keep page markup responsible only for display. Add a MySQL pool and idempotent schema initializer, then convert `src/store.ts` query-by-query. Package Astro standalone output as a private Node service behind a dedicated Apache virtual host.

**Tech Stack:** Astro 7 SSR, Node.js, TypeScript, `mysql2/promise`, Apache reverse proxy, MariaDB/MySQL.

## Constraints

- Production public base URL: `https://ai.lovemoney.live`.
- Local data source: MySQL `ailovemoney`; no PostgreSQL dependency remains.
- Only public HTTP port is 80; LikeShop ports 8086/8090/8095 remain unchanged.
- No credential is stored in Git, generated SQL, logs, or documentation.

### Task 1: Lock the requested public-site behavior with tests

**Files:** `test/rebrand-and-mysql.test.ts`

- [x] Assert the public URL and three blank community values.
- [x] Assert the shared layout has no Hero, GitHub, or X source and has a QQ placeholder.
- [x] Assert sponsors use only image markup and that the store does not import `pg`.
- [x] Focused rebrand/MySQL tests pass after implementation.

### Task 2: Replace the shared presentation shell and visible content

**Files:** `src/site.ts`, `src/layouts/PublicPage.astro`, `src/components/Sponsors.astro`, `src/i18n/*.ts`, `content/pages/**`, `content/guide/**`, `src/seo-routes.ts`, `.env.example`, `README*.md`

- [x] Set the brand URL to `https://ai.lovemoney.live` and define empty Telegram, X, and QQ values in the single site constants module.
- [x] Remove the Hero and project-GitHub UI; render Telegram, X, and QQ icons as non-navigating placeholders; use a text node for the announcement.
- [x] Render each sponsor as an image-only card with its accessible `alt` text.
- [x] Replace legacy self-brand text and URLs in runtime pages, localized content, SEO and repository readmes; retain unrelated third-party links.
- [x] Focused presentation assertions pass. About pages no longer render the old CardNav banner image.

### Task 3: Replace PostgreSQL with MySQL

**Files:** `package.json`, `src/database.ts`, `src/store.ts`, `scripts/init-mysql.mjs`, `test/mysql-store.test.ts`, `.env.example`, `README*.md`

- [x] Schema integration test initializes `ailovemoney` and required tables.
- [x] Runtime uses `mysql2`; PostgreSQL driver removed.
- [x] Public store queries use MySQL placeholders and keep existing return shapes.
- [x] Non-empty PostgreSQL snapshots (9 rows) migrated; shop tables were empty.
- [x] Focused database tests, typecheck, and build passed.

### Task 4: Package and validate the local release

**Files:** `scripts/export-ailovemoney.ps1`, `scripts/deploy-ai-lovemoney.ps1`, `scripts/deploy-ai-lovemoney-remote.sh`, `README*.md`

- [x] Local exporter: `scripts/export-mysql.ps1` (SQL stays outside Git).
- [x] Paramiko session uploads release/SQL and runs remote install; temp artifacts deleted.
- [x] Local `pnpm run build` and browser QA recorded in p004.

### Task 5: Deploy without disturbing LikeShop

**Server files:** `/etc/apache2/sites-available/ai.lovemoney.live.conf`, `/etc/systemd/system/ai-lovemoney.service`, `/www/wwwroot/ai.lovemoney.live`

- [x] Diagnosed Apache/Node/MySQL/disk; port 80 is LikeShop `dtch.yg2022.top` and was kept as a name-based vhost.
- [x] Did not remove LikeShop from port 80; added `ServerName ai.lovemoney.live`.
- [x] Imported `ailovemoney`, installed `/www/wwwroot/ai.lovemoney.live`, enabled `ai-lovemoney.service`.
- [x] Host-header and real-domain browser verification of `https://ai.lovemoney.live/` recorded in p006 QA.
- [x] LikeShop `8086/shop/`, `8090/mobile/`, `8095/admin/` still return HTTP 200.
