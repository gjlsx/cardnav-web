# CardNav Web Agent Rules

## Scope and sources of truth

- This file adds concise project behavior rules. Task execution, locks, tasklist fields, commit checkpoints, and archival remain governed by `.agent-rules.md`, `tasklist_rules.md`, and `taskexec/cardnav-web/`.
- Before changing collection behavior, read the relevant current documents: `docs/data-nav-and-collection.md`, `docs/collection-data-lifecycle.md`, `docs/collection-capture-engine.md`, and `scripts/collection/README.md`. Verify any material claim in the actual source and tests.
- Keep durable architecture decisions in the existing project documents and task-specific evidence in taskexec detail, log, and QA files. Do not create duplicate architecture/status documents unless the user explicitly approves them.

## Confirmed collection architecture

- Collection is raw-first: approved public source -> `collection_raw_payloads` / `collection_raw_records` -> explicit independent merge/import -> existing runtime tables and public snapshots. Do not add a second schema, a second staging pipeline, or a direct runtime-write path.
- Real network collection runs locally only, after an exact source allowlist and approval are configured. Do not crawl from `ai.lovemoney.live`, follow downstream merchant links, bypass robots/access controls, handle login or CAPTCHA, or clear existing runtime data after a source failure.
- Crawlee + Playwright is the approved direction for new browser collection adapters. Preserve the existing collector files as legacy until a separately approved deletion task; new CLI and GUI paths must not invoke them.
- The merge/import worker remains default-disabled, local, singleton, and serial. It reads completed raw batches only; it does not perform browser collection.

## Implementation and verification

- Keep new behavior aligned with the confirmed architecture. Do not add a fast-path script, mock-only protocol, UI-only operation, or alternate publish route that would bypass the normal raw -> merge/import lifecycle.
- Every new operational capability needs a reproducible one-line CLI path. A browser-visible change also needs verification through the actual local browser entry point; route or unit-test output alone is supporting evidence.
- Preserve unrelated working-tree edits. Prefer small scoped changes, remove only code made unused by the same approved change, and state pre-existing test failures separately.

## MySQL and sensitive data

- A collection batch uses one scoped MySQL session/transaction across reads, writes, and derived refreshes. Parameterize values, use bounded timeout/reconnect only for known transient failures, roll back before retry, and never reconnect per row or SQL statement.
- Never commit or log database credentials, connection strings, cookies, CAPTCHA data, tokens, private keys, exported dumps, or complete third-party response bodies. Raw public responses belong only in the local audit storage governed by the collection lifecycle.
