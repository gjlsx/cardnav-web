![](assets/banner.webp)

<h1 align="center">AI LoveMoney</h1>

<p align="center">
  <a href="README.md">中文</a> ·
  <strong>English</strong>
</p>

<p align="center">
  <strong>A one-stop guide to buying AI model accounts. It brings together AI gateways, card shops, official subscription price comparisons, model rankings, usage guides, and practical tools to help you avoid pitfalls and spend less.</strong>
</p>

<p align="center">
  <a href="https://ai.lovemoney.live">
    <img src="" alt="AI LoveMoney website" />
  </a>
  <a href="https://t.me/+AX9TXrzMaS04OWI1">
    <img src="https://img.shields.io/badge/Telegram-Group-26a5e4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram group" />
  </a>
  <a href="https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00">
    <img src="https://img.shields.io/badge/Support-Stripe-635bff?style=flat-square&logo=stripe&logoColor=white" alt="Support AI LoveMoney" />
  </a>
  <img src="https://img.shields.io/badge/QQ-1106704568-12b7f5?style=flat-square" alt="QQ group 1106704568" />
  <a href="">
    <img src="https://img.shields.io/badge/X-placeholder-000000?style=flat-square&logo=x&logoColor=white" alt="X placeholder" />
  </a>
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

AI LoveMoney brings AI model accounts, official subscriptions, gateway services, card shop merchants, model rankings, usage guides, and practical tools into one public entry point so users can choose, compare, search, and make better pre-purchase decisions faster.

For more on the thinking behind AI LoveMoney and why it was created, read [About AI LoveMoney](content/pages/en/about.md).

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
| Model rankings | View public reference rankings for coding, creative writing, math, text-to-image, and video generation. Video generation is currently an empty placeholder. Scores come from public pages, not this site’s live evaluation |
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

AI LoveMoney does not try to throw everything at you at once. It tries to put the order in a clearer sequence:

1. Check model rankings first to see which models matter for different tasks
2. Compare official subscription prices to understand regional price differences
3. When a third-party channel is needed, search merchants, products, stock, and prices on the homepage
4. Before placing an order, read Help to prepare network access, payment, delivery expectations, KYC, and risk-control basics
5. When it is time to operate, use tools such as IP cleanliness checks and Session conversion
6. Quality merchants can enter the listing flow through the submission entrance or view cooperation exposure options directly

## Help

[Help](https://ai.lovemoney.live/guide) is AI LoveMoney's usage path for new users. It is not a loose tutorial collection. It systematically separates the issues that are often mixed together, following the order of choosing a model, choosing a usage method, preparing network and payment basics, and then handling daily risk control.

The following are the original Markdown guide documents. Reading them directly on the [official website](https://ai.lovemoney.live/guide) is recommended for the best layout and browsing experience.

Guide Markdown rendering rules for cards, frontmatter, and internal links are documented in [AI LoveMoney Guide Markdown Rendering](content/guide/README.md).

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
npm install
cp .env.example .env
npm run dev
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
PUBLIC_SITE_URL=https://ai.lovemoney.live
ABUSEIPDB_API_KEY=
GREYNOISE_API_KEY=
```

### Common Commands

```bash
pnpm install
pnpm run dev
pnpm run seed:reference-samples
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
- Local collection console: `python scripts/collection/gui.py`

`seed:reference-samples` writes a bounded public reference sample set into local MySQL `ailovemoney` and the public snapshots. It is not live collection.

## Current implementation boundary

Canonical decisions: [data navigation and collection boundary](docs/data-nav-and-collection.md).

- Done: renamed three-locale nav, standard SKU aggregation, gateway/official/leaderboard reference samples, and internal model/plan relation queries. Production is display-only.
- Manual check: after seeding, open `/shops`, `/llm-gateway`, `/official-price`, and `/model-leaderboard` on <http://127.0.0.1:3101/>. Samples are labeled non-live and have no purchase outbound links.
- Requires per-source user approval: real HTTP collection, Windows/remote schedulers, auto-publishing staging to public snapshots. Unapproved sources must not make network requests.
- Existing partnership/submit forms stay; submissions are not auto-published.
- Source defaults: `enabled=false`, `interval_minutes=60`, `max_items_per_run=1000` (`0` = unlimited). `site.score=50` is a display initial value only.
- This site does not support Russian. `README.ru.md` has been removed; there is no Russian README, and Russian is not a supported public language.
- Passwords, SSH keys, connection strings, and SQL dumps stay out of this repository.

## Current production deployment

Public site: `https://ai.lovemoney.live/`  
The app is an Astro standalone Node process on `127.0.0.1:3101`. Apache ports 80 and 443 serve only `ai.lovemoney.live`. The database is server-local MySQL/MariaDB `ailovemoney`. LikeShop stays on `8086/8090/8095` and no longer uses port 80.

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

AI LoveMoney's software code is open sourced under the [GNU Affero General Public License v3.0](./LICENSE).

The `AI LoveMoney` and `AI LoveMoney` names, Logo, domain, visual brand, online production data, merchant data, product data, search data, guide content, screenshots, and public page copy are not licensed together with the software code. Before forking, secondary development, or deploying a public service, please read the [Data and Content License](./DATA_LICENSE.md) and [Brand and Trademark Policy](./TRADEMARKS.md), and avoid making users believe your service is the official website.


