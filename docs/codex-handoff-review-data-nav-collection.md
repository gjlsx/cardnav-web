# Codex 交接 Review：数据展示、示范数据、采集与导航

> 2026-08-29 纠偏：本文的原始“staging → 人工/规则批准 → 快照”方向继续保留，但现行实现合同改为固定统一 raw 格式、后续 merge/import 直接写运行时表即发布。请以 [collection-data-lifecycle.md](collection-data-lifecycle.md) 和 `tasklist08281547` p024–p028 为准；本文不能授权真实来源联网。

**给后续执行者：** 先读 [当前事实文档](data-nav-and-collection.md)。本文保留产品决策原文。  
**作者：** grok review（用户确认后的交接文档）  
**日期：** 2026-08-28  
**状态：** 导航、标准 SKU 聚合、中转/官方/排行示范数据和内部关联已在 `tasklist08281547` p001–p005 落地。真实 HTTP 采集、调度安装、自动 publish 仍须用户逐项批准；不要把本文当成采集授权。

相关已有文档（只作背景，冲突时以本文为准）：

- `docs/reference-data-audit.md`
- `docs/local-collection-brainstorm.md`
- `taskexec/cardnav-web/docs/backuptask/tasklist08280652.md`

---

## 1. 用户已确认的总方向

1. **卡网商品展示改成标准商品聚合**（方案 B 的产品形态）：一行一个标准 SKU，展示最低参考价、渠道数、有货渠道，点进去才是商家/渠道。对标 `https://priceai.cc/channels` 与 `https://www.openprice.cc/card-products` 的信息层级，不复制整页。
2. **采集按平台族做**（方案 B）：NewAPI/OneAPI 一类中转站、独角/LikeShop H5 一类卡网，一族一个适配器，而不是一域名一套 CSS。
3. **合作表单并行**（方案 C）：现有商家/中转站提交继续作为正规数据入口。
4. **三个聚合站仍是定时抓取目标**，但是**平台族抓取的补充**，不是主源。
5. **采集必须是本机软件形态**：脚本/CLI、可定时、结果入 MySQL；生产站只读展示。不要把爬虫跑在 `ai.lovemoney.live` 对外 IP 上。
6. **同一中转站或同一卡网站出现在多个来源时，采用优先级覆盖**（见第 4 节）。
7. **当前必须先改导航文案，并给目前空着的板块补示范数据**（见第 5、6 节）。

---

## 2. 上一轮样例工作结论（必须带着改）

已完成且可保留：

- `reference_data_sources` + `shop_products` 来源/标准名/平台/类型/币种/渠道数/`is_sample`/`sampled_at`
- 种子同时写实体表和 `public_snapshot_entries`（`shop-products` / `shop-products-packed`）
- `/shops` 有「参考样例 / 非实时」提示，无购买外链
- 未启动自动抓取

必须修正（不要只加数据、不改结构）：

| 优先级 | 问题 | 要求 |
|---|---|---|
| P1 | `/shops` 仍是商家 SKU 行，不是标准商品聚合 | 增加「标准商品」默认视图：一行一 `standard_product`，最低价 + 渠道数 + 有货渠道；商家明细为下钻或切换视图 |
| P1 | 没有权威 SKU 表 | 新增 `catalog_products`（slug、platform、product_type、显示名、别名）。未知别名进人工队列，禁止采集时自动乱建品 |
| P1 | `/llm-gateway`、`/official-price` 无示范数据 | 见第 6 节，必须种子 + 快照 + 页面可见 |
| P2 | `shop_sites.url = 来源页#siteId` | 商家官网 URL 与目录来源 URL 分开；未核实官网时商家 url 留空，不要伪造 |
| P2 | 种子覆盖 `popular-search-terms` 快照 | 样例种子不得改热搜快照 |
| P2 | `reference_data_sources.is_sample` 默认 TRUE | 默认 FALSE，样例再显式打开 |
| P2 | packed 协议仍 `v:1` 尾部追加字段 | 若扩展元组，bump 版本或保证 unpack 按长度兼容并补测试 |
| P3 | 无 `(source_id, standard_product, site_id)` 自然键 | 自动化前补唯一键；种子不要只靠删 `reference-*` |

---

## 3. 标准商品聚合（展示，P0）

对标 PriceAI / OpenPrice 的列表语义，不是抄皮肤。

**默认 `/shops` 视图（标准商品）：**

- 列/卡片字段至少：平台、标准商品名、类型（成品号/订阅/CDK/API 等）、最低参考价、币种、渠道总数、有货渠道、缺货渠道（可空）、采样时间、参考样例标记
- 一行一个 `catalog_products.slug` / `standard_product`
- 最低价来自该 SKU 下优先级最高的有效报价（见第 4 节），不是随便第一条
- 点击标准商品后看到渠道/商家列表；样例商家仍无购买跳转

**可保留的商家视图：** 现有按商家分组作为次要切换，不得作为默认。

**首页热门卡网：** 与标准商品视图同一套聚合数据，不要再只展示碎 SKU。

页面必须继续显示：公开参考样例、非实时、到原平台核验。

---

## 4. 采集架构与冲突优先级（软件 + 定时 + MySQL）

### 4.1 形态

- 本机 CLI（建议 `scripts/collection/`，当前不要先写万能爬虫）
- 定时：本机调度（Windows 计划任务或等价），只跑 collect；**默认不得自动 publish 到公开快照**，除非用户以后另行批准
- 写入 MySQL `ailovemoney`：staging →（人工/规则批准）→ 实体表 + `public_snapshot_entries` 事务切换
- 生产站点不发起抓取

### 4.2 来源分层

```text
主源：平台族适配器
  - 中转站族：公开 API（如 NewAPI/OneAPI 的 models/pricing JSON）
  - 卡网族：独角数卡 / LikeShop H5 / 同类模板的公开目录
补充：合作表单提交（已有 partnership / gateway-submit）
再补充：三个聚合站定时抓取
  1. https://priceai.cc/channels
  2. https://cardnav.xyz/
  3. https://www.openprice.cc/card-products
```

三个聚合站**保留为定时目标**，但只补充「族适配器还没有覆盖到的标准商品/渠道」。禁止把聚合站当作唯一真相。

### 4.3 同一对象多源时的覆盖顺序

对象 = 同一个中转站，或同一个卡网站（按规范化 host / 登记的 `site_id` 对齐）。

**从高到低：**

1. **该站自己的 API**（文档化或公开 JSON）
2. **该站实际网站的网页采集**（公开目录页）
3. **三个聚合站**（仅补充），聚合站内部再排序：
   1. `https://priceai.cc/`
   2. `https://cardnav.xyz/`
   3. `https://www.openprice.cc/`（openprice）

规则：

- 高优先级源一旦给出该对象的有效字段，低优先级源**不得覆盖**这些字段。
- 低优先级源可以填补高优先级源缺失的字段（例如 API 有模型价、聚合站有渠道数）。
- 报价/库存行的自然键建议：`canonical_site + standard_product + product_type`；来源只作为 provenance，不作为展示主键。
- 记录 `source_id`、`source_rank`、`observed_at`、`collected_at`，页面展示的采样时间用 `observed_at`。

### 4.4 合规（不变）

- 不登录、不验证码、不购物车、不绕过 robots/条款
- 不存整页 HTML、Cookie、账号、交付说明
- 默认不下载第三方商品图
- User-Agent 可识别；每域名低频、单并发；变更用 ETag/内容 hash，没变不解析
- `cardnav.xyz` / PriceAI / OpenPrice 即使作为定时目标，实现前仍需在来源登记里写明频率与字段白名单；没有登记则 CLI 退出

### 4.5 实现顺序（给 Codex 排期）

先做第 5、6 节（导航 + 空板块示范数据 + 标准商品视图 + catalog），再开采集 CLI。  
采集首个可运行切片（仍须用户最终点头定时器）：dry-run 一个平台族源 **或** 一个聚合站一页 ≤10 条进 staging，不自动 publish。

---

## 5. 导航改名（当前必须做）

只改**显示文案**，**路由不要改**：`/llm-gateway`、`/official-price`、`/guide` 保持不变。

中文（必须按此字面）：

| 键 | 现文案 | 新文案 |
|---|---|---|
| `nav.llmGateway` | 中转站排行 | **中转网站** |
| `nav.mobileLlmGateway` | 中转站 | **中转网站**（过长可仍用「中转网站」） |
| `nav.officialPrice` | 官方订阅比价 | **官方网站** |
| `nav.mobileOfficialPrice` | 官方订阅 | **官方网站** |
| `nav.guide` | 向导 | **帮助** |
| `nav.mobileGuide` | 向导 | **帮助** |

英文 / 俄文必须同步，建议：

| 键 | en | ru |
|---|---|---|
| `llmGateway` / `mobileLlmGateway` | Gateway sites | Сайты-шлюзы |
| `officialPrice` / `mobileOfficialPrice` | Official sites | Официальные сайты |
| `guide` / `mobileGuide` | Help | Помощь |

还要扫一遍首页卡片、SEO 标题、`openGuide`、`buyingGuide`、`guideTitle` 等用户可见入口：导航叫「帮助 / 中转网站 / 官方网站」时，首页入口不要继续写「向导」「中转站排行」「官方订阅比价」。页面 H1 可以保留说明性副标题（例如「中转网站」主标题 + 「API 渠道与模型价格」副标题），但主导航必须用新名字。

文件：`src/i18n/zh.ts`、`en.ts`、`ru.ts`；导航消费处 `src/layouts/PublicPage.astro` 已用 `t.nav.*`，一般不用改 href。补测试：公开文案快照/品牌测试里若写死旧导航字符串，一并更新。

---

## 6. 示范数据（当前必须做）

用户指出：**中转网站、官方网站目前都没有示范数据**，需要像卡网商品一样，用公开参考样例填起来并在页面看见。帮助页已有 Markdown 向导内容，此项以改名为准，不必编造假文章。

### 6.1 中转网站 `/llm-gateway`

写入并同步快照：

- `gateway_sites`：至少 4–8 个样例站（可从 cardnav 首页/公开列表可见的短字段来：站名、host、模型覆盖摘要、采样时间）
- `gateway_model_prices`：每个样例站少量公开可见的模型价（缺单位则价格留空，禁止编造 latency/可用率）
- `public_snapshot_entries`：`gateway-sites`、`gateway-models`（以及页面实际读取的 key）
- `is_sample` / 来源 / 非实时提示：与 `/shops` 同一套可见语义（网关表若还没有这些列，按最小原则补，或在快照 DTO 里带 `isSample`）

页面：`/llm-gateway` 与首页「热门中转」模块必须出现这些样例；样例站不要设置未核实的邀请/购买外链（`invite_url` 可空）。

### 6.2 官方网站 `/official-price`

写入并同步快照：

- `official_prices`：至少覆盖 ChatGPT / Claude / Gemini / Grok 等常见套餐在 2–3 个地区的**公开参考样例**（价格标明采样、非实时）
- `public_snapshot_entries`：`official-price-catalog`、`official-prices`（以 `src/store.ts` 实际读取的 key 为准）
- 首页「低价官方订阅 / 官方网站」入口要能读到数据，不要空白卡

数据必须标注参考样例；不要写成「官方实时价保证」。

### 6.3 卡网 `/shops`

在已有 9 条样例基础上：

- 引入 `catalog_products` 并把现有 `standard_product` 挂上去
- 默认列表改为标准商品聚合
- 同一 SKU 若被多个样例来源提到，展示时按第 4.3 节优先级合成一行

### 6.4 种子约束

- 扩 `scripts/seed-reference-samples.ts`（或拆 `seed-gateway-samples` / `seed-official-samples`，但一个 `pnpm` script 入口即可）
- 幂等；只动 `reference-*` / `is_sample` 行
- **禁止**覆盖 `popular-search-terms`
- 本地 MySQL `ailovemoney` 与生产发布流程与上一轮相同：先本地验证，再独立站；不碰 LikeShop `8086/8090/8095`
- 浏览器必须从导航进入：首页 → 中转网站、官方网站、帮助、卡网商品；确认新名字 + 非空示范数据 + 样例提示

---

## 7. Codex 建议任务切分

可建新 tasklist，建议顺序：

1. **P0 导航三语改名** + 测试里旧文案
2. **P0 catalog_products + /shops 标准商品默认视图** + 现有样例迁移
3. **P0 中转网站示范数据**（表 + 快照 + `/llm-gateway` + 首页模块）
4. **P0 官方网站示范数据**（表 + 快照 + `/official-price` + 首页模块）
5. **P1 本机采集 CLI 骨架**（registry、dry-run、staging、优先级合并）；三个聚合站适配器作为补充源登记进去，**先不要挂 Windows 定时器**
6. **P1 文档**：更新 `docs/local-collection-brainstorm.md` 为本文第 4 节；README 导航名称

采集定时器、生产自动入库：单独等用户确认后再做。

---

## 8. 验收清单

- [ ] 桌面+移动导航：中转网站 / 官方网站 / 帮助（zh/en/ru）
- [ ] `/guide` 仍能打开原向导内容，只是名叫帮助
- [ ] `/shops` 默认标准商品聚合；有样例标记；无购买外链
- [ ] `/llm-gateway` 有样例站点/价格或明确样例空态以外的真实样例行
- [ ] `/official-price` 有样例套餐/地区价
- [ ] 首页对应模块不再空白
- [ ] `pnpm test`、`pnpm run typecheck`、`pnpm run build` 通过
- [ ] 浏览器从真实入口点进上述页；生产若发布，LikeShop 三端口仍 200
- [ ] 未启用定时抓取、未对未登记源发批量请求

---

## 9. 明确不要做

- 不改路由 path，不把 `/guide` 改成 `/help`
- 不把三个聚合站当唯一数据源，也不要删掉它们的定时目标身份
- 不在本任务里对生产站跑爬虫
- 不编造中转站延迟/可用率、不编造官方实时价
- 不恢复首页 Hero，不把旧 CardNav 横幅加回来
