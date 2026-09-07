![](assets/banner.webp)

<h1 align="center">AIGATE</h1>

<p align="center">
  <strong>中文</strong> ·
  <a href="README.en.md">English</a>
</p>

<p align="center">
  <strong>可信 AI 选择与购买决策入口。比较模型、价格和渠道，理解依据与风险，找到合适的下一步。</strong>
</p>

<p align="center">
  <a href="https://aigate.live">
    AIGATE 官网
  </a>
  <a href="https://t.me/+AX9TXrzMaS04OWI1">
    <img src="https://img.shields.io/badge/Telegram-%E7%BE%A4%E7%BB%84-26a5e4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram 群组" />
  </a>
  <a href="https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00">
    <img src="https://img.shields.io/badge/%E6%94%AF%E6%8C%81%E4%BD%9C%E8%80%85-Stripe-635bff?style=flat-square&logo=stripe&logoColor=white" alt="支持 AIGATE" />
  </a>
</p>

<p align="center">
  <a href="#产品简介">产品简介</a> ·
  <a href="#一站式能力">一站式能力</a> ·
  <a href="#面向用户">面向用户</a> ·
  <a href="#使用方式">使用方式</a> ·
  <a href="#帮助">帮助</a> ·
  <a href="#当前实现边界">当前实现边界</a> ·
  <a href="#本地运行">本地运行</a> ·
  <a href="#贡献">贡献</a> ·
  <a href="#license">License</a>
</p>

---

![](assets/screenshot.webp)

## 产品简介

AIGATE 帮助用户理解 AI 模型、官方订阅、中转站、价格和使用风险，更快完成可信比较并找到合适的下一步。网站现有目录、参考榜单、帮助和工具；持续自扩展的决策与商业闭环是已确认的发展方向。

## 战略与路线图

- [产品战略](docs/PRODUCT_STRATEGY.md)：已确认的目标、用户价值、商业模式和历史整合结论。
- [目标与里程碑路线图](docs/ROADMAP.md)：推进顺序、验收条件、指标和未来实施输入。
- [当前进度](docs/CURRENT_STATUS.md)：已实现能力、带日期的验证证据和下一步。

收入优先固定赞助、明确标注的付费排名和广告，随后对接我方中转站与商业站，并披露自营/关联关系。自然评分与自然榜单保持独立。SEO/GEO 是获客手段，核心衡量每周可信比较后的有效站外导流用户数。AI 选购代理、商家增长系统与完整排名治理属于后续里程碑，不能将这些规划当作已上线能力。

## 公开运营入口

- 赞助入口：<https://buy.stripe.com/cNi8wRgiq26I1Ese0V0Fi00>。页面在顶部社群图标后显示“我要赞助”，折叠菜单显示“支持作者”，商务合作页提供完整赞助卡。
- Telegram 群：<https://t.me/+AX9TXrzMaS04OWI1>。
- QQ 群：`1106704568`，页面会展示并允许复制群号。
- 中转站收录邮箱：<xiu.juan2love@gmail.com>。

这些公开值的唯一代码来源是 `src/site.ts`；修改时必须同时检查顶部导航、折叠菜单、商务合作页、中转站收录弹窗和实际网页中的 Telegram 链接，避免复制出不同地址。

## 一站式能力

| 板块 | 说明 |
| --- | --- |
| 帮助 | 把模型选择、使用方式、实操准备、商家判断、网络环境、支付方式、KYC 和日常风控串成一条完整路径，帮助用户在真正下单前先把关键判断补齐 |
| 卡网商品 | 按标准 SKU 聚合第三方卡网报价：一行一个权威商品，展示最低参考价、渠道数和有货渠道；商家明细为下钻，不是默认视图 |
| 排名参考 | 模型表现、中转参考、价格参考；结合来源和采样时间阅读，同单位价格才作比较，上游参考不等于本站独立评分 |
| 官方网站 | 对比 ChatGPT、Claude、Gemini、Grok 等官方订阅在不同地区的价格和折算，并可跳到关联卡网商品与支持该模型族的中转网站 |
| 工具集 | 集中提供 ChatGPT Session 转换工具、IP 纯净度检测，以及 Codex 凭证助手、Outlook 快速取件等外部辅助工具，帮助用户在注册、登录、支付、导入和格式处理前先完成快速检查与处理 |
| 商家提交与合作 | 提供商家提交、公开收录、赞助位和合作入口，让优质商家获得更清晰的展示和曝光路径 |

## 面向用户

- 想把 AI 真正用起来，但不想在模型、账号、网络、支付和商家信息之间反复跳的人
- 想比较 ChatGPT、Claude、Gemini、Grok 等订阅价格和地区差异的人
- 想查找 AI 账号、订阅、卡密、成品号或相关服务购买入口的人
- 想先看商品库存、价格、商家活跃度，再决定是否进入具体站点的人
- 想了解商家筛选、交付格式、网络环境、支付方式和风控注意事项的人
- 想提交站点、获得收录、争取优质曝光或进一步合作的商家

## 使用方式

AIGATE不是把所有东西都塞给你，而是尽量把顺序排清楚一点：

1. 先看排名参考中的模型表现，知道不同任务下大概该看谁
2. 再看官方网站价格参考，弄明白不同地区的价格差异
3. 需要第三方渠道时，再去首页搜商家、商品、库存和价格
4. 下单前看看帮助，把网络、支付、交付、KYC 和风控这几件事补齐
5. 真到要操作时，再用 IP 纯净度检测、Session 转换这些工具
6. 优质商家可以通过提交入口进入收录流程，或者查看合作曝光入口

## 帮助

[帮助](https://aigate.live/guide) 是AIGATE给新手用户准备的使用路径。它不是零散教程集合，而是按“先选模型、再选使用方式、再补齐网络与支付准备、最后处理日常风控”的顺序，系统性的把容易混在一起的问题拆开讲清楚。

以下为向导内容的 Markdown 原始文档，推荐直接在 [官网](https://aigate.live/guide) 阅读，以获得最佳排版与浏览体验。

向导 Markdown 的卡片、frontmatter 和站内链接渲染规则见 [AIGATE向导 Markdown 渲染说明](content/guide/README.md)。

| 向导 | 说明 |
| --- | --- |
| [开始向导](content/guide/zh/000-start-here.md) | 从 Start here 开始，先确定模型、再选使用方式、再补齐工具与支付等准备项。 |
| [一、选择你想使用的 AI 大模型](content/guide/zh/100-choose-model.md) | 先判断你是要顶级模型能力，还是低门槛和低成本，再决定是否继续这条向导。 |
| [二、选择 AI 订阅使用方式](content/guide/zh/200-choose-usage-method.md) | 对比中转站、成品号、代充、自充、自建等五种大模型使用方式的门槛、风险和适用人群。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.1 AI 大模型 API 中转站](content/guide/zh/211-usage-api-gateway.md) | 通过 API 中转站快速获得大模型调用能力，适合低门槛试用、多模型接入和轻量开发调试。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.2 AI 大模型成品账号购买与登录](content/guide/zh/212-usage-ready-account.md) | 购买已开通订阅的成品账号并直接登录，适合快速体验原生网页和客户端功能。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.3 AI 大模型自备账号第三方代充](content/guide/zh/213-usage-third-party-top-up.md) | 自己保留账号，由第三方商家代为开通或续费官方订阅，适合已有账号但无法自行付款的用户。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.4 AI 大模型官方订阅充值](content/guide/zh/214-usage-self-register.md) | 自己准备网络、手机号和支付通道，独立注册并订阅官方账号，适合长期重度用户。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[2.5 自建 AI 大模型中转站](content/guide/zh/215-usage-self-hosted-gateway.md) | 购买官方额度并自建中转接口，适合有技术基础、需要团队共享和内部接入的用户。 |
| [三、AI 订阅实操准备与选购避坑](content/guide/zh/300-practical-prep.md) | 补齐网络与云主机配置、准备支付通道、了解订阅区域价差以及认识卡网和发货格式。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.1 认识卡网与选购避坑](content/guide/zh/310-merchant-overview.md) | 了解什么是虚拟商品卡网平台，以及如何安全选购海外大模型账号与服务。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[如何挑选靠谱商家](content/guide/zh/311-choose-reliable-merchant.md) | 购买 AI 账号或虚拟商品时，从商品数量、热门覆盖、平台属性、支付渠道和社群活跃度等维度判断商家信任度。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[常见账号发货格式说明](content/guide/zh/312-common-delivery-formats.md) | 先判断商家发的是账密、四段 RT，还是各种 JSON 凭证，再决定能不能直接登录或应该导入什么工具。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.2 网络环境与主机准备](content/guide/zh/320-network-env-overview.md) | 梳理独立注册、登录与付款时的网络配置、IP 风险控制及海外主机租用流程。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[科学上网与 VPN](content/guide/zh/321-tool-vpn.md) | 解决地区访问限制，并尽量保证后续注册、登录和订阅时的地区与 IP 稳定匹配。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[云服务器推荐](content/guide/zh/322-tool-vps.md) | 为自建节点或自建中转站准备更可控的海外主机环境。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[IP 纯净度检查](content/guide/zh/323-tool-ip-check.md) | 在注册、登录和付款前，先粗略筛掉明显高风险的出口 IP。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[国外手机号验证](content/guide/zh/324-tool-phone-verification.md) | 解决注册验证码和后续二次验证问题，避免一次性号码导致账号后续卡死。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.3 国际支付与价差](content/guide/zh/330-payment-overview.md) | 先看订阅的地区价格差异，再选择合适的国际支付渠道和防风控建议。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[订阅价格地区差异](content/guide/zh/331-region-pricing-differences.md) | 同一个订阅套餐在不同国家和地区的定价可能差很多。对比不同地区的实际开销与支付门槛。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[App Store 支付](content/guide/zh/332-payment-app-store.md) | 通过对应地区的 Apple ID 和礼品卡完成应用商店内订阅支付。 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Google Play Store 支付](content/guide/zh/333-payment-google-play.md) | 使用目标地区 Google 账号和 Google Play 完成应用内订阅支付。 |
| &nbsp;&nbsp;&nbsp;&nbsp;[3.4 认识 KYC 风控](content/guide/zh/340-kyc-verification.md) | 了解什么是 KYC 身份认证风控，为什么以 Claude 为代表的平台容易触发，以及在没有海外身份时该如何应对。 |
| [四、AI 订阅使用期间的风控与日常避坑](content/guide/zh/400-daily-usage-risk.md) | 梳理海外大模型账号在日常使用期间常见的风控触发点与避坑建议。 |

## 本地运行

```bash
pnpm install
# 仅首次配置；已有 .env 时保留
# PowerShell: Copy-Item .env.example .env
pnpm dev
```

默认读取当前目录下的 `.env`。

### 环境变量

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

### 常用命令

```bash
pnpm install
pnpm run dev
pnpm test
pnpm run typecheck
pnpm run build
pnpm start
```

### 本机启动与检查

网站开发服务由 Astro 管理器运行：

```bash
pnpm dev
```

- 网站：<http://127.0.0.1:3101/>（状态/停止：`pnpm exec astro dev status`、`pnpm exec astro dev stop`）
- 新采集 CLI：`python -m scripts.crawlee_collection check-config`
- Legacy 总控台：`python scripts/collection/gui.py`

`pnpm run seed:reference-samples` 仅供独立样例环境，会写数据库；已有真实数据时不要作为启动步骤运行。

## 当前实现边界

- 现有入口包括标准 SKU 商品、中转站与模型详情、官方网站、排名参考（模型表现/中转参考/价格参考）、帮助和工具；公开内容支持中文与英文。
- 当前采集入口是 `scripts/crawlee_collection/` 的 CLI；共用 `catch.config`，精确来源白名单，raw → 独立 merge/import → 运行表与快照。公开数据页面读取这些结果，生产服务器不运行采集器。
- `scripts/collection/` 保留 legacy 控制台和历史代码；新采集路径见 [采集器 README](scripts/crawlee_collection/README.md)。工作区的新 GUI 文件尚未纳入版本控制，克隆仓库后以已跟踪 CLI 为准。
- 样例、上游参考和采样数据不等同实时评测；上游 rank 和初始 `site.score=50` 不能冒充新的综合评分。
- 现有合作/提交、赞助展示和部分点击记录可复用，完整双榜治理、有效导流归因与商业闭环仍需验证。
- 新来源、运行频率和自动化按既有规则批准；采集与 merge 循环默认关闭。实际参数由 `catch.config` 和 [来源代码](scripts/crawlee_collection/sources.py) 确认，不照抄旧默认值。
- 秘密、数据库连接串和 SQL dump 不进入仓库；不支持俄语。

数据架构见 [数据导航边界](docs/data-nav-and-collection.md) 和 [采集生命周期](docs/collection-data-lifecycle.md)。旧架构文档中的品牌/日期仅描述当时事实，当前入口和任务进度以 [CURRENT_STATUS](docs/CURRENT_STATUS.md) 为准。

## 当前生产部署

公开站点：[AIGATE](https://aigate.live/)。2026-09-03 已记录的发布验证显示，旧域 `ai.lovemoney.live` 以 308 转向新域并保留路径和查询。应用是回环 `127.0.0.1:3101` 上的 Astro standalone Node，Apache 80/443 提供网站和旧域跳转；数据库为服务器 MySQL/MariaDB `ailovemoney`。LikeShop 保持 `8086/8090/8095`。本次文档更新未重新验证在线状态。

- 发布目录：`/www/wwwroot/ai.lovemoney.live`
- 进程：`ai-lovemoney.service`（systemd，开机自启）
- 数据导出/导入流程见 [MySQL 迁移说明](docs/mysql-migration.md)
- 回滚位置：`/www/wwwroot/ai.lovemoney.live-backups`；停站时禁用 `ai-lovemoney` 并 `a2dissite ai.lovemoney.live.conf`，不要改 LikeShop 虚拟主机

密码、SSH 密钥、数据库 dump 和服务器 `.env` 不写入本仓库。

### 目录结构

```text
cardnav-web/
├── content/              # 向导、关于页、隐私政策等 Markdown 内容
├── public/               # favicon、OG 图和静态资源
├── src/layouts/          # Astro 公共页面布局
├── src/pages/            # Astro 页面和 API 路由
├── src/scripts/          # 首页、工具页等前端交互脚本
├── src/store.ts          # 公开数据读取
└── src/seo-routes.ts     # sitemap、robots、llms.txt 页面清单
```

## 贡献

欢迎通过 Issue 或 Pull Request 提交：

- 页面、样式和交互体验改进
- 公开向导内容补充
- 工具页能力优化
- 搜索、筛选和排序体验建议
- 文档、环境变量和本地运行说明修正

## License

AIGATE 的软件代码使用 [GNU Affero General Public License v3.0](./LICENSE) 开源。

`AIGATE` 名称、Logo、域名、视觉品牌、线上生产数据、商家数据、商品数据、搜索数据、指南内容、截图和公开页面文案不随软件代码授权。Fork、二次开发或部署公开服务时，请阅读 [数据与内容授权](./DATA_LICENSE.md) 和 [品牌与商标政策](./TRADEMARKS.md)，并避免让用户误认为你的服务是官方网站。


