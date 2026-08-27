# ai.lovemoney.live Implementation Plan

> **For agentic workers:** Execute sequentially in the current checkout. This repository has no taskexec contract; preserve unrelated changes and use normal Git commits.

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

- [ ] Assert the public URL and three blank community values.
- [ ] Assert the shared layout has no Hero, GitHub, or X source and has a QQ placeholder.
- [ ] Assert sponsors use only image markup and that the store does not import `pg`.
- [ ] Run `npm test -- test/rebrand-and-mysql.test.ts`; expected result before implementation: failure because old CardNav values and PostgreSQL code still exist.

### Task 2: Replace the shared presentation shell and visible content

**Files:** `src/site.ts`, `src/layouts/PublicPage.astro`, `src/components/Sponsors.astro`, `src/i18n/*.ts`, `content/pages/**`, `content/guide/**`, `src/seo-routes.ts`, `.env.example`, `README*.md`

- [ ] Set the brand URL to `https://ai.lovemoney.live` and define empty Telegram, X, and QQ values in the single site constants module.
- [ ] Remove the Hero and project-GitHub UI; render Telegram, X, and QQ icons as non-navigating placeholders; use a text node for the announcement.
- [ ] Render each sponsor as an image-only card with its accessible `alt` text.
- [ ] Replace legacy self-brand text and URLs in runtime pages, localized content, SEO and repository readmes; retain unrelated third-party links.
- [ ] Rerun the focused test; expected result: all its presentation assertions pass.

### Task 3: Replace PostgreSQL with MySQL

**Files:** `package.json`, `src/database.ts`, `src/store.ts`, `scripts/init-mysql.mjs`, `test/mysql-store.test.ts`, `.env.example`, `README*.md`

- [ ] Add a failing integration test that initializes `ailovemoney`, checks required tables, writes a minimal public snapshot, and reads it through the public store.
- [ ] Add `mysql2`, expose a shared MySQL pool/close function, and create repeatable DDL for every table queried by `src/store.ts`.
- [ ] Convert every query to MySQL placeholders/functions and preserve existing return shapes and ordering.
- [ ] Add an initializer that optionally imports compatible PostgreSQL rows before PostgreSQL is retired; because the discovered source tables are empty, it must succeed with an empty import.
- [ ] Run focused database tests, then `npm test` and `npm run typecheck`.

### Task 4: Package and validate the local release

**Files:** `scripts/export-ailovemoney.ps1`, `scripts/deploy-ai-lovemoney.ps1`, `scripts/deploy-ai-lovemoney-remote.sh`, `README*.md`

- [ ] Add a local exporter that runs `mysqldump` with a transient environment password and emits a disposable SQL artifact outside the Git tree.
- [ ] Add a deployment driver that builds Astro, uploads the release and SQL via Paramiko/SFTP, and deletes only its own temporary artifacts.
- [ ] Validate with `npm run build`, start the built service with local MySQL, and browser-check the homepage at the development port.

### Task 5: Deploy without disturbing LikeShop

**Server files:** `/etc/apache2/sites-available/ai.lovemoney.live.conf`, `/etc/systemd/system/ai-lovemoney.service`, `/www/wwwroot/ai.lovemoney.live`

- [ ] Diagnose Apache listeners, enabled sites, Node availability, MySQL service, disk capacity, and existing port-80 owner before mutation.
- [ ] Back up and remove only an existing port-80 non-LikeShop site when present.
- [ ] Import the local MySQL export into server-local `ailovemoney`, install the release, enable the service/vhost, and reload Apache.
- [ ] Verify `http://206.119.177.74/` with `Host: ai.lovemoney.live`, then verify the domain in a browser and capture the rendered homepage.
- [ ] Verify `dtch.yg2022.top:8086/shop/`, `:8090/mobile/`, and `:8095/admin/` still return their existing applications.
