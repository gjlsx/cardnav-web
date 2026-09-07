---
scope: cardnav-web
updated_at: 2026-09-07 08:11 Asia/Hong_Kong
timezone: Asia/Hong_Kong
tags: [aigate, strategy, roadmap, documentation, taskexec]
summary: Product decisions are confirmed and consolidated into PRODUCT_STRATEGY and ROADMAP; September 3 release evidence is recorded, while measurement and commercial implementation remain future milestones.
---

# Current Status

## Current product and approved direction

- Brand/domain: **AIGATE**, [aigate.live](https://aigate.live/). Latest recorded release (2026-09-03) verified the legacy ai.lovemoney.live redirect; live availability was not rechecked for this documentation task.
- Product goal: credible AI purchasing decisions and measurable referrals. SEO/GEO are acquisition methods.
- Monetization order: fixed sponsorship, labeled paid placement and advertising; then referrals to specified operator-owned gateway/commercial sites with affiliation disclosure.
- Organic ranking and scoring remain independent of sponsorship or ownership. Transparent composite scoring is approved as a direction, but its formula and full UI separation still need implementation and verification.
- Priority innovations: purchasing assistant and merchant growth system. The primary metric is weekly qualified outbound-referral users after a credible comparison.
- Current documents: [PRODUCT_STRATEGY](PRODUCT_STRATEGY.md) and [ROADMAP](ROADMAP.md). The historical August 31 strategy and combined roadmap were consolidated and removed by user request; Git retains their history.

## Implemented foundation and remaining gaps

- Public surfaces: standard-SKU shops, gateway/model details, official subscription references, ranking-reference tabs, help/tools, cooperation/submission, sponsor and community entries; Chinese and English public content.
- September 3 added a shared back-to-top control and refreshed the allowlisted data through the existing local raw → merge/import → runtime/snapshot lifecycle.
- Existing sponsor pinning and partial Umami/search/click events are reusable. They do not yet prove an independent organic/sponsored ranking product, qualified referral attribution, advertiser billing, recurring revenue or a merchant analytics system.
- No verified traffic/Search Console baseline, GEO citation trend, new composite-score method, owned-site asset list or revenue baseline is recorded. These remain ROADMAP M0-M7 work.
- READMEs now point to the two approved documents and describe current branding and dated evidence. Older architecture docs retain some historical brand wording; runtime source and newer task evidence govern current facts.

## Runtime boundaries and entry points

- Local site: http://127.0.0.1:3101/; check managed state with `pnpm exec astro dev status` before browser validation.
- Tracked collector CLI: `python -m scripts.crawlee_collection check-config`; [collector commands](../scripts/crawlee_collection/README.md).
- New GUI `scripts/crawlee_collection/gui.py` exists locally but is untracked. A fresh checkout should use the tracked CLI. Legacy console: `python scripts/collection/gui.py`.
- MySQL database: ailovemoney; settings only from local .env MYSQL_* values. No secrets in docs or task evidence.
- Exact approved sources feed existing raw tables; explicit local singleton/serial merge/import writes runtime tables and snapshots. All operational controls use catch.config; no arbitrary source URLs.
- Production serves public data and does not run a collector/scheduler. LikeShop ports 8086/8090/8095 stay isolated. Public browser routes do not collect or write collection data.
- Source facts, upstream ranks, editorial judgment and sponsorship are distinct. Do not present upstream rank or initial score 50 as a newly verified AIGATE score.

## Latest recorded verification

The following is historical repository evidence, not tests rerun on September 7.

- September 3 collection QA: configured allowlisted sources completed without source failures; 1,269 raw records, 1,268 runtime writes; Crawlee suite 42 tests passed. [Data QA](../taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p002.md)
- September 3 release QA: Node tests 106/106, typecheck 0 errors/warnings/hints, successful build; 426 gateway sites, 2,344 gateway model-price rows and 11 public snapshots.
- Browser verified old-domain arrival at aigate.live/llm-gateway and the back-to-top interaction. LikeShop 8086/8090/8095 returned 200; no production collector/timer. [Release QA](../taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p003.md)
- September 7 task is documentation only. Link, decision-coverage, backup and Git checks are recorded in [documentation QA](../taskexec/cardnav-web/docs/qa/p1_codex_t09070222.p003.md).

## Task state and preserved local changes

- [Task index](../taskexec/cardnav-web/tasklistall.md) is authoritative for active/archive locations.
- tasklist08300447 remains active: grok p001-p007 remain todo; p008-p022 done. Do not claim those grok rows under this documentation task.
- tasklist08311831 and tasklist09030447 are archived and complete as documentation/release tasks respectively; that does not mark business milestones complete.
- tasklist09070222 delivers the approved strategy/roadmap and README/status closure; its implementation/status commits and final archive are recorded in the task index.
- Existing uncommitted .gitignore, AGENTS.md, collection engine notes, database.py, local GUI, database notes and caches are preserved. They are not part of this documentation delivery.

## Next TODO

Start with ROADMAP M0 measurement-baseline, then M1 trust-and-ranking. The strategic direction no longer needs another choice round. Resolve scoring methodology, specific sponsor contracts and owned-site domains when their implementation tasks need them; no production commercial change is implied by completing these documents.

## Durable references

- [Data/navigation](data-nav-and-collection.md)
- [Collection lifecycle](collection-data-lifecycle.md)
- [Capture engine](collection-capture-engine.md)
- Runtime table notes are currently an untracked local document; do not rely on them being in a fresh checkout.
