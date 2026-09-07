---
scope: cardnav-web
updated_at: 2026-08-31 18:31 Asia/Hong_Kong
timezone: Asia/Hong_Kong
tags: [aigate, production, collection, ranking-reference, roadmap, taskexec]
summary: AIGATE is live on aigate.live with a read-only public decision surface, local raw-first collection, explicit merge/import, and verified old-domain redirect; sustainable acquisition and monetization loops remain roadmap work.
---

# Current Status

This file is the concise canonical handoff for current project state. Task-level evidence stays in `taskexec/cardnav-web/`; durable collection rules stay in the linked architecture documents.

## Current product identity and production entry

- Public brand and primary domain: **AIGATE** at `https://aigate.live/`.
- The legacy `https://ai.lovemoney.live/` host redirects with HTTP 308 to the same path and query on `aigate.live`; the browser also preserves the URL fragment.
- The production site is Astro SSR on the independent `ai-lovemoney` service. LikeShop remains isolated on ports `8086`, `8090`, and `8095`.
- Production is read-only. Collection and its scheduler do not run on the production server.
- `README.md` and `README.en.md` still contain a mixture of AIGATE, AI LoveMoney, the primary domain, and the legacy domain. Treat this as documentation drift, not as the runtime source of truth.

## Progress summary from three lenses

### 1. Product and user journey

Implemented public surfaces include:

- AI usage guidance from model choice through usage method, network/payment preparation, KYC, and daily risk control;
- card-shop SKU aggregation, gateway-site/model detail, official subscription price references, model-performance references, and comparable gateway model prices;
- `/ranking-reference` with model, gateway reference, and price tabs while preserving legacy leaderboard deep links;
- practical tools, merchant/gateway submission, sponsorship/cooperation, Telegram, and QQ entry points;
- Chinese and English public content. Russian is not supported and must not be restored as a claimed public language.

The user can currently discover, compare, inspect sources and continue to an external/community entry. The repository does not yet document a complete acquisition-to-conversion-to-revenue feedback loop.

### 2. Data and engineering

- The only approved collection path is: exact allowlisted public source -> `collection_raw_payloads` / `collection_raw_records` -> explicit local singleton merge/import -> existing runtime tables and public snapshots.
- The active collector is `scripts/crawlee_collection/`, using the same CLI and `catch.config` for collection and merge controls. `scripts/collection/` remains legacy and is retained for audit/rollback.
- PriceAI, CardNav and the Hvoy open JSON reference have bounded source contracts. The Hvoy source populates only a reference snapshot; it does not overwrite AIGATE site scores, hand-maintained fields, or price data.
- Dynamic SEO routes, sitemap families, locale alternates, robots policy and `llms.txt` exist. Gateway model pages already use a minimum data gate before entering the sitemap.
- Collection stays local, serial and default-off. It does not follow downstream merchant links, handle login/CAPTCHA, or bypass access controls.

### 3. Business and growth

- Present assets: high-intent comparison pages, practical guides/tools, merchant submission, cooperation/sponsor surfaces, community entry points, and some click/search endpoints.
- Present defensibility: normalized cross-source data, raw audit trail, freshness/source semantics, standard SKU/model relationships, and a controlled publish transaction.
- Missing proof: no repository-grounded evidence yet of Search Console baseline, query-to-page demand map, attributable outbound conversion, paid merchant product, recurring revenue, retention cohort, or B2B data/API customer.
- Therefore “top ranking”, “self-expanding”, and “sustainable traffic business” are project objectives, not current achievements.

## Confirmed architecture and safety boundary

- The public Astro site reads runtime tables and public snapshots; it must not collect sources or write collection data through browser routes.
- Programs and their order are hardcoded. Config may select only registered source IDs and operational intervals; it cannot add arbitrary URLs.
- Merge/import is explicit, local, singleton and serial. It reads completed raw batches and writes runtime tables/snapshots in one scoped MySQL transaction.
- Source facts, AIGATE editorial judgments, user feedback and commercial placement are separate concepts. Never convert an upstream rank into an AIGATE score or allow sponsorship to alter organic ordering.
- Secrets, full third-party bodies, dumps, credentials, cookies and CAPTCHA data never enter Git, README, QA reports or task logs.

## Verified entry points

- Managed local site: `http://127.0.0.1:3101/`; check with `pnpm exec astro dev status` before browser validation.
- New collector CLI: `python -m scripts.crawlee_collection check-config`.
- New collector GUI: `python -m scripts.crawlee_collection.gui`.
- Legacy console retained for history: `python scripts/collection/gui.py`.
- Local MySQL settings come only from repository-root `.env` `MYSQL_*`; never copy their values into documentation.
- Production deployment uses `python scripts/deploy/publish_ai_lovemoney.py` and must independently regression-check LikeShop.

## Latest recorded verification (historical evidence, not rerun on 2026-08-31 18:31)

- 2026-08-29: PriceAI collect/merge recorded 67 valid raw records and 67 runtime writes; the then-relevant Crawlee suite recorded 20 passes and legacy collection suite 55 passes.
- 2026-08-30: Hvoy exact-allowlist collection recorded 765 valid raw records; explicit merge wrote the reference snapshot without creating gateway sites. Related Python suite recorded 30 passes, `pnpm test` 102 passes, and typecheck 0 errors/warnings.
- 2026-08-30: desktop and mobile browser evidence covered the gateway-reference and price-reference tabs plus the gateway-to-reference entry.
- 2026-08-31: redirect release preflight recorded `pnpm test` 104/104, typecheck 0 errors/warnings, and a successful build.
- 2026-08-31: production evidence recorded old-domain HTTP/HTTPS 308, real-browser arrival on `aigate.live`, LikeShop `8086/8090/8095` HTTP 200, no production collector/timer, `gateway_sites=422`, `gateway_model_prices=2283`, and `public_snapshot_entries=11`.

## Known gaps and risks

- Documentation drift: the READMEs and some older architecture text still name the legacy brand/domain or describe tasks that have since completed.
- Measurement gap: traffic, indexing, freshness, outbound click, qualified lead and revenue baselines are not documented in a common metric dictionary.
- Quality-at-scale gap: sitemap eligibility exists for gateway models, but there is no project-wide publish/noindex/prune gate for every future programmatic page family.
- Trust gap: sources are attributed, but an AIGATE-wide editorial/ranking methodology, correction policy, commercial disclosure and merchant verification ladder are not yet one public contract.
- Commercial gap: sponsor/cooperation entries exist, but pricing, inventory, attribution, service levels and separation from organic results are not yet a verified product.
- Operating gap: collection is controlled, but content opportunity discovery, evidence drafting, review, expiry and refresh are not yet one repeatable pipeline.

## Active tasklists

- `taskexec/cardnav-web/tasklist08300447.md`: active because p001-p007 remain assigned to `grok`; p008-p022 are completed. Do not claim the `grok` rows as `codex` work.
- `taskexec/cardnav-web/tasklist08311831.md`: current `codex` documentation task for status, three-option strategy design, and goals/milestones/roadmap.

## Next TODO

Finish `tasklist08311831.md`, then ask the user to choose a strategic posture from the three documented alternatives before creating implementation tasklists. The default recommendation may guide sequencing, but it is not approval to change ranking logic, collection scope, commercial placement, or production behavior.

## Durable references

- Data/navigation facts: [`data-nav-and-collection.md`](data-nav-and-collection.md)
- Raw-to-runtime lifecycle: [`collection-data-lifecycle.md`](collection-data-lifecycle.md)
- Capture engine decision: [`collection-capture-engine.md`](collection-capture-engine.md)
- Runtime table roles: [`数据库说明.md`](数据库说明.md)
