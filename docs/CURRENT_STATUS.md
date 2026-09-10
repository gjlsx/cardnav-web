---
scope: cardnav-web
updated_at: 2026-09-10 17:20 Asia/Hong_Kong
timezone: Asia/Hong_Kong
tags: [aigate, strategy, roadmap, documentation, taskexec]
summary: External leaderboard reference disclosure and a default-off local measurement foundation were implemented and locally verified; the 2026-09-10 code review repaired its remaining P1 acceptance gaps. Real-source onboarding, self-tests and production telemetry remain unapproved.
---

# Current Status

## Current product and approved direction

- Brand/domain: **AIGATE**, [aigate.live](https://aigate.live/). Latest recorded release (2026-09-03) verified the legacy ai.lovemoney.live redirect; live availability was not rechecked for this documentation task.
- Product goal: credible AI purchasing decisions and measurable referrals. SEO/GEO are acquisition methods.
- Monetization order: fixed sponsorship, labeled paid placement and advertising; then referrals to specified operator-owned gateway/commercial sites with affiliation disclosure.
- Organic ranking and scoring remain independent of sponsorship or ownership. Transparent composite scoring is approved as a direction, but its formula and full UI separation still need implementation and verification.
- Priority innovations: purchasing assistant and merchant growth system. The primary metric is weekly qualified outbound-referral users after a credible comparison.
- Current documents: [PRODUCT_STRATEGY](PRODUCT_STRATEGY.md) and [ROADMAP](ROADMAP.md). The historical August 31 strategy and combined roadmap were consolidated and removed by user request; Git retains their history.
- September 8–9 review preserves those decisions: M0 minimum measurement and M1 core trust may progress together, while full scores and growth evidence are separate outputs. Qualified official-site referrals count equally; fixed sponsorship needs review, expiry/pause and delivery checks. [Design review](../taskexec/cardnav-web/docs/issues/ISSUE-005.md)

- September 10 sequencing clarification: external leaderboard references first, open-source self-tests afterward; scoring remains a product requirement. Competitor parity plus focused differentiators, first-party measurement and attributed external platform aggregates are recorded in the two canonical documents.
- September 10 code review corrected the local measurement's Hong Kong day boundary, concurrent idempotency, consented channel/outbound events, report aggregation and retention cleanup. The repair is tracked in [ISSUE-006](../taskexec/cardnav-web/docs/issues/ISSUE-006.md); it does not enable telemetry or create a real baseline.

## Implemented foundation and remaining gaps

- Public surfaces: standard-SKU shops, gateway/model details, official subscription references, ranking-reference tabs, help/tools, cooperation/submission, sponsor and community entries. Source supports Chinese, English and Russian with public language-switching entries; language quality/browser coverage was not retested in this documentation task.
- September 3 added a shared back-to-top control and refreshed the allowlisted data through the existing local raw → merge/import → runtime/snapshot lifecycle.
- Existing sponsor pinning and partial Umami/search/click events are reusable. They do not yet prove an independent organic/sponsored ranking product, qualified referral attribution, advertiser billing, recurring revenue or a merchant analytics system.
- No verified traffic/Search Console baseline, GEO citation trend, new composite-score method, owned-site asset list or revenue baseline is recorded. These remain ROADMAP M0-M7 work.
- READMEs and current data/deployment docs align with the approved documents. Historical technical plans are explicitly marked as such; old checkboxes and brand wording are not active execution instructions. Routine deployment excludes sample seed.

## Runtime boundaries and entry points

- Local site: http://127.0.0.1:3101/; check managed state with `pnpm exec astro dev status` before browser validation.
- Tracked collector CLI: `python -m scripts.crawlee_collection check-config`; [collector commands](../scripts/crawlee_collection/README.md).
- New GUI `scripts/crawlee_collection/gui.py` exists locally but is untracked. A fresh checkout should use the tracked CLI. Legacy console: `python scripts/collection/gui.py`.
- MySQL database: ailovemoney; settings only from local .env MYSQL_* values. No secrets in docs or task evidence.
- Exact approved sources feed existing raw tables; explicit local singleton/serial merge/import writes runtime tables and snapshots. All operational controls use catch.config; no arbitrary source URLs.
- Single-worker operation is a required constraint. The current worker guard is process-local, not proof of cross-process exclusion; do not launch simultaneous import commands. Default-off configuration does not block explicitly invoked CLI collection/import.
- Production serves public data and does not run a collector/scheduler. LikeShop ports 8086/8090/8095 stay isolated. Public browser routes do not collect or write collection data.
- Source facts, upstream ranks, editorial judgment and sponsorship are distinct. Do not present upstream rank or initial score 50 as a newly verified AIGATE score.

## Latest recorded verification

The following is historical repository evidence, not product tests rerun in the September 7–9 documentation work.

- September 3 collection QA: configured allowlisted sources completed without source failures; 1,269 raw records, 1,268 runtime writes; Crawlee suite 42 tests passed. [Data QA](../taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p002.md)
- September 3 release QA: Node tests 106/106, typecheck 0 errors/warnings/hints, successful build; 426 gateway sites, 2,344 gateway model-price rows and 11 public snapshots.
- Browser verified old-domain arrival at aigate.live/llm-gateway and the back-to-top interaction. LikeShop 8086/8090/8095 returned 200; no production collector/timer. [Release QA](../taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p003.md)
- September 7 task is documentation only. Link, decision-coverage, backup and Git checks are recorded in [documentation QA](../taskexec/cardnav-web/docs/qa/p1_codex_t09070222.p003.md).
- Follow-up documentation/source consistency checks are recorded in [closure QA](../taskexec/cardnav-web/docs/qa/p1_codex_t09070820.p001.md). This corrects the earlier documentation claim that Russian was unsupported; no language code was changed.

## Task state and preserved local changes

- [Task index](../taskexec/cardnav-web/tasklistall.md) is authoritative for active/archive locations.
- [tasklist09100118](../taskexec/cardnav-web/docs/backuptask/tasklist09100118.md) is archived after implementing traceable sample/reference display and default-off local session-level measurement. New-source crawling, self-tests, public telemetry activation and deployment remain excluded.
- tasklist08300447 remains active: grok p001-p007 remain todo; p008-p022 done. Do not claim those grok rows under this documentation task.
- tasklist08311831 and tasklist09030447 are archived and complete as documentation/release tasks respectively; that does not mark business milestones complete.
- tasklist09070222 delivers the approved strategy/roadmap and README/status closure; its implementation/status commits and final archive are recorded in the task index.
- tasklist09070820 closes related technical/deployment docs and historical-plan status; see the task index for its implementation/status/archive record.
- Existing uncommitted .gitignore, AGENTS.md, collection engine paragraph, database.py, local GUI, database notes and caches are preserved. Only the separate historical-status banner in the engine document belongs to this delivery; the pre-existing paragraph edit is excluded.

## Next TODO

Next work requires separate approval for exact external source/usage permission, benchmark repository/revision/data/fees, production telemetry/privacy review, and any commercial deployment. Session counts are not weekly unique users; north-star remains unavailable. This does not finish M0/M1, self-tests, traffic baselines or commercial readiness.

## Durable references

- [Data/navigation](data-nav-and-collection.md)
- [Collection lifecycle](collection-data-lifecycle.md)
- [Capture engine](collection-capture-engine.md)
- Runtime table notes are currently an untracked local document; do not rely on them being in a fresh checkout.
