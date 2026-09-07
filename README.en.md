![](assets/banner.webp)

<h1 align="center">AIGATE</h1>

<p align="center">
  <a href="README.md">中文</a> ·
  <strong>English</strong>
</p>

<p align="center">
  <strong>A credible AI selection and purchasing decision hub. Compare models, prices and providers, understand evidence and risks, and find an appropriate next step.</strong>
</p>

<p align="center">
  <a href="https://aigate.live">
    AIGATE website
  </a>
  <a href="https://t.me/+AX9TXrzMaS04OWI1">
    <img src="https://img.shields.io/badge/Telegram-Group-26a5e4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram group" />
  </a>
  <a href="https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00">
    <img src="https://img.shields.io/badge/Support-Stripe-635bff?style=flat-square&logo=stripe&logoColor=white" alt="Support AIGATE" />
  </a>
  <img src="https://img.shields.io/badge/QQ-1106704568-12b7f5?style=flat-square" alt="QQ group 1106704568" />
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#all-in-one-capabilities">Capabilities</a> ·
  <a href="#who-it-is-for">Who It Is For</a> ·
  <a href="#how-to-use-it">How To Use It</a> ·
  <a href="#help">Help</a> ·
  <a href="#current-implementation-boundary">Current boundary</a> ·
  <a href="#local-development">Local Development</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="#license">License</a>
</p>

---

![](assets/screenshot.webp)

## Overview

AIGATE helps users understand AI models, official subscriptions, gateway services, prices and usage risks, compare credible evidence, and find an appropriate next step. Existing directories, reference rankings, guides and tools form the starting point for the approved decision and referral strategy.

## Strategy and roadmap

- [Product strategy](docs/PRODUCT_STRATEGY.md): confirmed purpose, user value, business model and reconciled historical decisions (Chinese).
- [Goals and milestone roadmap](docs/ROADMAP.md): sequence, acceptance gates, metrics and future implementation inputs (Chinese).
- [Current status](docs/CURRENT_STATUS.md): implemented capabilities, dated verification evidence and next steps.

Fixed sponsorship, clearly labeled paid placement and advertising come first, followed by referrals to specified operator-owned gateways and commercial sites with ownership/affiliation disclosure. Organic scores and rankings stay independent. SEO/GEO are acquisition channels; the core metric is weekly users making qualified outbound referrals after a credible comparison. The purchasing assistant, merchant growth system and complete ranking governance remain roadmap work.

## Public operating links

- Sponsor: <https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00>.
- Telegram group: <https://t.me/+AX9TXrzMaS04OWI1>.
- QQ group: `1106704568`.
- Gateway listing email: <xiu.juan2love@gmail.com>.

These values have one code source in `src/site.ts`. When changing one, check the header, mobile menu, partnership page, gateway submission dialog, and all rendered Telegram links together.

## All-in-One Capabilities

| Section | Description |
| --- | --- |
| Help | Connect model selection, usage methods, practical setup, merchant evaluation, network environment, payment methods, KYC, and daily risk control into one complete path so users can fill in key judgments before placing an order |
| Card shops | Aggregates third-party quotes as standard SKUs: one canonical product per row, with a lowest reference price, channel count, and in-stock channels. Merchant details are a drill-down, not the default view |
| Ranking references | Model performance, gateway references and comparable prices, with source and sampling context. Upstream rankings are not independent AIGATE scores |
| Official sites | Compare ChatGPT, Claude, Gemini, and Grok official plan prices across regions, then jump to related shop SKUs and gateway sites that support the model family |
| Toolset | Provides ChatGPT Session conversion, IP cleanliness checks, and external helper tools such as Codex credential assistant and Outlook quick pickup to help users complete quick checks and processing before registration, login, payment, import, or format conversion |
| Merchant submission and cooperation | Provides merchant submission, public listing, sponsorship slots, and cooperation entrances so quality merchants can get clearer display and exposure paths |

## Who It Is For

- People who want to use AI seriously without repeatedly jumping between model, account, network, payment, and merchant information
- People who want to compare ChatGPT, Claude, Gemini, Grok, and other subscription prices across regions
- People looking for purchase entrances for AI accounts, subscriptions, activation codes, ready-made accounts, or related services
- People who want to check stock, prices, and merchant activity before deciding whether to enter a specific site
- People who want to understand merchant selection, delivery formats, network environments, payment methods, and risk-control precautions
- Merchants who want to submit a site, get listed, earn quality exposure, or discuss further cooperation

## How To Use It

AIGATE does not try to throw everything at you at once. It tries to put the order in a clearer sequence:

1. Check model performance in Ranking references to see which models matter for different tasks
2. Compare official subscription prices to understand regional price differences
3. When a third-party channel is needed, search merchants, products, stock, and prices on the homepage
4. Before placing an order, read Help to prepare network access, payment, delivery expectations, KYC, and risk-control basics
5. When it is time to operate, use tools such as IP cleanliness checks and Session conversion
6. Quality merchants can enter the listing flow through the submission entrance or view cooperation exposure options directly

## Help

[Help](https://aigate.live/guide) is AIGATE's usage path for new users. It is not a loose tutorial collection. It systematically separates the issues that are often mixed together, following the order of choosing a model, choosing a usage method, preparing network and payment basics, and then handling daily risk control.

The following are the original Markdown guide documents. Reading them directly on the [official website](https://aigate.live/guide) is recommended for the best layout and browsing experience.

Guide Markdown rendering rules for cards, frontmatter, and internal links are documented in [AIGATE Guide Markdown Rendering](content/guide/README.md).

| Guide | Description |
| --- | --- |
| [Start Here](content/guide/en/000-start-here.md) | Start here to choose a model first, then choose a usage method, then prepare tools, payment, and related basics. |
| [1. Choose the AI Model You Want to Use](content/guide/en/100-choose-model.md) | First decide whether you need top-tier model capability or a lower barrier and lower cost, then decide whether to continue through this guide. |
| [2. Choose an AI Subscription Usage Method](content/guide/en/200-choose-usage-method.md) | Compare five ways to use AI models: API gateway, ready-made accounts, third-party top-up, self-registration, and self-hosted gateway, including their barriers, risks, and suitable users. |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.1 AI Model API Gateway](content/guide/en/211-usage-api-gateway.md) | Quickly obtain model API access through an API gateway, suitable for low-barrier trials, multi-model access, and lightweight development/debugging. |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.2 Buying and Logging Into Ready-Made AI Model Accounts](content/guide/en/212-usage-ready-account.md) | Buy an account that already has an active subscription and log in directly, suitable for quickly trying native web and client features. |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.3 Third-Party Top-Up for Your Own AI Model Account](content/guide/en/213-usage-third-party-top-up.md) | Keep your own account and let a third-party merchant activate or renew an official subscription, suitable for users who already have an account but cannot pay by themselves. |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.4 Official AI Model Subscription Top-Up](content/guide/en/214-usage-self-register.md) | Prepare network access, phone number, and payment channel yourself, then register and subscribe independently, suitable for long-term heavy users. |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.5 Self-Hosted AI Model Gateway](content/guide/en/215-usage-self-hosted-gateway.md) | Buy official quota and host your own gateway API, suitable for users with technical background who need team sharing and internal integration. |
| [3. Practical AI Subscription Preparation and Buying Pitfalls](content/guide/en/300-practical-prep.md) | Prepare network and cloud host configuration, payment channels, subscription regional price differences, and understand card shops and delivery formats. |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.1 Understanding Card Shops and Buying Pitfalls](content/guide/en/310-merchant-overview.md) | Understand virtual goods card shop platforms and how to safely buy overseas AI model accounts and services. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[How to Choose a Reliable Merchant](content/guide/en/311-choose-reliable-merchant.md) | When buying AI accounts or virtual goods, judge merchant reliability from product count, popular coverage, platform attributes, payment channels, community activity, and more. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Common Account Delivery Formats](content/guide/en/312-common-delivery-formats.md) | First identify whether the merchant delivers username/password, four-part RT, or JSON credentials, then decide whether you can log in directly or which tool to import into. |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.2 Network Environment and Host Preparation](content/guide/en/320-network-env-overview.md) | Organize network configuration, IP risk control, and overseas host rental workflows for registration, login, and payment. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Proxy/VPN Access](content/guide/en/321-tool-vpn.md) | Resolve regional access restrictions while keeping region and IP stable for later registration, login, and subscription. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Cloud Server Recommendations](content/guide/en/322-tool-vps.md) | Prepare a more controllable overseas host environment for self-hosted nodes or self-hosted gateway services. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[IP Cleanliness Check](content/guide/en/323-tool-ip-check.md) | Before registration, login, and payment, roughly filter out obviously high-risk exit IPs. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Foreign Phone Number Verification](content/guide/en/324-tool-phone-verification.md) | Solve registration verification codes and later two-factor checks, avoiding one-time numbers that may lock the account later. |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.3 International Payments and Regional Price Differences](content/guide/en/330-payment-overview.md) | Review regional subscription price differences first, then choose a suitable international payment channel and risk-control approach. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Subscription Regional Price Differences](content/guide/en/331-region-pricing-differences.md) | The same subscription plan may cost very different amounts across countries and regions. Compare actual cost and payment barriers across regions. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[App Store Payment](content/guide/en/332-payment-app-store.md) | Complete in-app subscription payment through an Apple ID and gift cards for the corresponding region. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Google Play Store Payment](content/guide/en/333-payment-google-play.md) | Complete in-app subscription payment with a target-region Google account and Google Play. |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.4 Understanding KYC Risk Control](content/guide/en/340-kyc-verification.md) | Understand what KYC identity verification risk control is, why platforms represented by Claude often trigger it, and what to do without overseas identity documents. |
| [4. Daily Risk Control and Pitfalls During AI Subscription Use](content/guide/en/400-daily-usage-risk.md) | Summarize common risk-control triggers and avoidance suggestions during everyday use of overseas AI model accounts. |

## Local Development

```bash
pnpm install
# First setup only; preserve an existing .env
# PowerShell: Copy-Item .env.example .env
pnpm dev
```

By default, the project reads `.env` from the current directory.

### Environment Variables

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=ailovemoney
PORT=3101
PUBLIC_SITE_URL=https://aigate.live
ABUSEIPDB_API_KEY=
GREYNOISE_API_KEY=
```

### Common Commands

```bash
pnpm install
pnpm run dev
pnpm test
pnpm run typecheck
pnpm run build
pnpm start
```

### Local start and check

The Astro development manager owns the local website process:

```bash
pnpm dev
```

- Website: <http://127.0.0.1:3101/> (`pnpm exec astro dev status` / `pnpm exec astro dev stop`)
- Current collector CLI: `python -m scripts.crawlee_collection check-config`
- Legacy console: `python scripts/collection/gui.py`

`pnpm run seed:reference-samples` is for isolated sample environments and writes to the database. Do not run it as a startup step against existing real data.

## Current implementation boundary

- Existing surfaces include standard SKU aggregation, gateway/model details, official plans, ranking references (model performance, gateway references and comparable prices), guides and tools. Public content supports Chinese and English.
- The current collector CLI is in `scripts/crawlee_collection/`, with one `catch.config` and an exact source allowlist: raw → independent merge/import → runtime tables and snapshots. Public data pages read those results; the production server does not run collection.
- `scripts/collection/` retains the legacy console and historical code. See the [collector README](scripts/crawlee_collection/README.md). The newer GUI file is currently untracked; a fresh clone should use the tracked CLI.
- Samples, upstream references and captured observations are not live independent evaluations. An upstream rank or initial `site.score=50` is not the planned composite score.
- Submission/cooperation, sponsored display and some click tracking exist. Full organic/sponsored separation, qualified referral attribution and a commercial feedback loop still need verification.
- New sources, cadence and automation follow existing approval rules; collection and merge loops default to off. Read actual parameters from `catch.config` and the [source registry](scripts/crawlee_collection/sources.py).
- Secrets, connection strings and SQL dumps stay out of Git. Russian is not supported.

See [data/navigation boundaries](docs/data-nav-and-collection.md) and the [collection lifecycle](docs/collection-data-lifecycle.md). Older architecture documents retain historical branding; use [CURRENT_STATUS](docs/CURRENT_STATUS.md) for current entry points and task state.

## Current production deployment

Public site: [AIGATE](https://aigate.live/). The recorded 2026-09-03 verification shows the legacy `ai.lovemoney.live` host redirecting with HTTP 308 while preserving the path and query. Astro standalone Node runs on loopback `127.0.0.1:3101`; Apache serves the site and old-domain redirects on 80/443. The database is server-local MySQL/MariaDB `ailovemoney`. LikeShop remains on `8086/8090/8095`. This documentation update did not recheck live availability.

- Release directory: `/www/wwwroot/ai.lovemoney.live`
- Process: `ai-lovemoney.service` (systemd, enabled)
- Data export/import: [MySQL migration notes](docs/mysql-migration.md)
- Rollback copies: `/www/wwwroot/ai.lovemoney.live-backups`. To take the site down, disable `ai-lovemoney` and `a2dissite ai.lovemoney.live.conf`. Do not edit LikeShop vhosts.

Do not commit passwords, SSH keys, database dumps, or the server `.env`.

### Directory Structure

```text
cardnav-web/
├── content/              # Guides, about page, privacy policy, and other Markdown content
├── public/               # favicon, OG image, and static assets
├── src/layouts/          # Shared Astro page layouts
├── src/pages/            # Astro pages and API routes
├── src/scripts/          # Homepage, tool pages, and other frontend interaction scripts
├── src/store.ts          # Public data reads
└── src/seo-routes.ts     # sitemap, robots, and llms.txt page list
```

## Contributing

Issues and Pull Requests are welcome for:

- Page, style, and interaction improvements
- Public guide content additions
- Tool page capability improvements
- Search, filtering, and sorting experience suggestions
- Documentation, environment variable, and local runtime fixes

## License

AIGATE's software code is open sourced under the [GNU Affero General Public License v3.0](./LICENSE).

The `AIGATE` name, Logo, domain, visual brand, online production data, merchant data, product data, search data, guide content, screenshots, and public page copy are not licensed together with the software code. Before forking, secondary development, or deploying a public service, please read the [Data and Content License](./DATA_LICENSE.md) and [Brand and Trademark Policy](./TRADEMARKS.md), and avoid making users believe your service is the official website.


