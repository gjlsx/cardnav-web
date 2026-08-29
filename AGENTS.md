# CardNav Web Agent Rules

## Scope and sources of truth

- This file adds concise project behavior rules. Task execution, locks, tasklist fields, commit checkpoints, and archival remain governed by `.agent-rules.md`, `tasklist_rules.md`, and `taskexec/cardnav-web/`.
- Before changing collection behavior, read the relevant current documents: `docs/data-nav-and-collection.md`, `docs/collection-data-lifecycle.md`, `docs/collection-capture-engine.md`, and `scripts/collection/README.md`. Verify any material claim in the actual source and tests.
- Keep durable architecture decisions in the existing project documents and task-specific evidence in taskexec detail, log, and QA files. Do not create duplicate architecture/status documents unless the user explicitly approves them.

## General operating guardrails

- Follow the global alert policy: schedule the prescribed alert when programmer intervention is needed and play one completion alert when entering idle.
- A message beginning `q:` is question-only: answer without modifying files, running task workflows, builds, or commits unless the user explicitly changes that scope.
- For multi-step work, give a brief `Step 1` / `Step 2` / `Validation` plan before edits. Prefer the smallest final-architecture-aligned solution; do not add one-off abstractions or temporary bypasses.
- For internal code evidence, use an absolute Windows path with an optional line number. Do not invent URL/URI-style local paths. User-facing final responses must still follow the platform's required clickable absolute file-link format.

## Local targets and stack boundaries

- The managed local Astro/Node site is currently `http://127.0.0.1:3101/`. Before browser validation, check `pnpm exec astro dev status`; do not assume the generic Astro port 4321.
- The local collection control surface is `python scripts/collection/gui.py`. There is no NocoDB administration service in this repository.
- MySQL defaults to `127.0.0.1:3306`, database `ailovemoney`; actual settings are read only from the local `.env` `MYSQL_*` values. Never expose them.
- The public Astro site only reads runtime tables and public snapshots. It must not collect sources or write collection data through a browser route.
- Current task state, resumable evidence, and verification live in `taskexec/cardnav-web/`. `docs/CURRENT_STATUS.md` does not exist and may be created only with explicit user approval.

## Confirmed collection architecture

- Collection is raw-first: approved public source -> `collection_raw_payloads` / `collection_raw_records` -> explicit independent merge/import -> existing runtime tables and public snapshots. Do not add a second schema, a second staging pipeline, or a direct runtime-write path.
- Real network collection runs locally only, after an exact source allowlist and approval are configured. Do not crawl from `ai.lovemoney.live`, follow downstream merchant links, bypass robots/access controls, handle login or CAPTCHA, or clear existing runtime data after a source failure.
- Crawlee + Playwright is the approved direction for new browser collection adapters. Preserve the existing collector files as legacy until a separately approved deletion task; new CLI and GUI paths must not invoke them.
- The merge/import worker remains default-disabled, local, singleton, and serial. It reads completed raw batches only; it does not perform browser collection.

## Implementation and verification

- Keep new behavior aligned with the confirmed architecture. Do not add a fast-path script, mock-only protocol, UI-only operation, or alternate publish route that would bypass the normal raw -> merge/import lifecycle.
- Every new operational capability needs a reproducible one-line CLI path. Astro/Node changes need targeted `pnpm run typecheck`, `pnpm test`, or `pnpm run build` evidence as applicable. A browser-visible change also needs verification through the actual local browser entry point; route, build, or unit-test output alone is supporting evidence.
- Preserve unrelated working-tree edits. Prefer small scoped changes, remove only code made unused by the same approved change, and state pre-existing test failures separately.

## MySQL and sensitive data

- A collection batch uses one scoped MySQL session/transaction across reads, writes, and derived refreshes. Parameterize values, use bounded timeout/reconnect only for known transient failures, roll back before retry, and never reconnect per row or SQL statement.
- Never commit or log database credentials, connection strings, cookies, CAPTCHA data, tokens, private keys, exported dumps, or complete third-party response bodies. Raw public responses belong only in the local audit storage governed by the collection lifecycle.
