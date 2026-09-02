# Back To Top, Collection Refresh, and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global, accessible fixed back-to-top action, refresh approved local collection data, and publish the verified result.

**Architecture:** The shared public layout owns the semantic button and the shared shell script owns its display and click behavior. The existing Crawlee CLI remains the only collector and its explicit raw then merge/import stages update local runtime tables. The established publish script transfers only build output and local database state to the isolated production site.

**Tech Stack:** Astro, browser JavaScript, Node test runner, Python Crawlee/Playwright, local MySQL, existing VPS publish script.

## Global Constraints

- The button is fixed in the lower-right corner and appears only after one viewport of page scrolling.
- Collection uses only `scripts/crawlee_collection/catch.config` source IDs and never follows merchant links, logs in, or bypasses access controls.
- Raw collection and merge/import stay separate; merge runs only after a successful collection batch.
- VPS deployment must preserve LikeShop 8086/8090/8095, remote `.env`, and the absence of production collectors/timers.

---

### Task 1: Shared back-to-top control

**Files:**
- Modify: `src/layouts/PublicPage.astro`
- Modify: `src/scripts/public-shell.js`
- Create: `test/back-to-top.test.ts`

- [ ] Add a failing source-contract test for a hidden `data-back-to-top` button, its accessible label, threshold behavior, and `window.scrollTo` smooth behavior.
- [ ] Run `pnpm exec tsx --test test/back-to-top.test.ts` and confirm it fails before implementation.
- [ ] Render the fixed button in the shared public layout and implement a small `initBackToTop()` function that toggles `hidden` on scroll and scrolls to top on click.
- [ ] Re-run the targeted test, `pnpm run typecheck`, and verify the long `/llm-gateway` page in the 3101 browser by scrolling then clicking the control.

### Task 2: Approved local collection refresh

**Files:**
- Read: `scripts/crawlee_collection/catch.config`
- Read: `scripts/crawlee_collection/README.md`
- Create: `taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p002.md`

- [ ] Run `python -m scripts.crawlee_collection check-config`, then `python -m scripts.crawlee_collection collect --all`.
- [ ] Require a zero-failure collector result with a returned batch ID. If it fails, record partial state and do not merge.
- [ ] Run `python -m scripts.crawlee_collection merge-once --batch <returned-batch-id>` and record only IDs/counts, never public raw bodies or credentials.
- [ ] Confirm the local 3101 gateway page reads the refreshed runtime data.

### Task 3: Isolated VPS release

**Files:**
- Read: `howtorunvpsnew.md`
- Read: `scripts/deploy/publish_ai_lovemoney.py`
- Create: `taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p003.md`

- [ ] Run full local tests, typecheck, and build.
- [ ] Run `python scripts/deploy/publish_ai_lovemoney.py` and accept only a successful verified release.
- [ ] Verify old-domain origin HTTP/HTTPS redirects, new-domain browser rendering, LikeShop 8086/8090/8095, and no production collection process/timer.
