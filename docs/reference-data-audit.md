# 公开参考数据审计（2026-08-28）

> 历史样例审计，不是当前数据量、schema 缺口或来源授权清单。当前实现/验证见 [CURRENT_STATUS](CURRENT_STATUS.md)，采集授权边界见 [数据导航与采集](data-nav-and-collection.md)；保留原文以说明早期决策依据。

## 结论

三站的共同核心不是“商品详情页”，而是一个可比较的**标准产品 × 商家/渠道 × 采样时点**列表：访客先按平台/类别筛选，再看最低参考价、供给/库存、渠道数和更新时间，最后自行到原平台核验。AI LoveMoney 当前 MySQL 已能承载站点、商品、价格、库存和刷新时间，但无法明确表达数据来源、标准化产品、平台/类型、渠道聚合和“参考样例”身份；这些是本次唯一需要补齐的字段。

本审计仅读取公开页面；没有登录、没有调用隐含接口、没有批量抓取。浏览器在本机临时保存了三张视觉审计截图（未加入仓库、未作为本站公开素材），用于确认页面由表格/卡片混合组成。第三方页面图像、商标和完整页面截图不进入生产构建，以避免错误的授权暗示和热链依赖。

## 观察来源与可用结构

| 来源 | 采样方式 | 页面可见结构 | 本次可采样的短字段 | 不采用内容 |
|---|---|---|---|---|
| `https://cardnav.xyz/` | 公开首页、浏览器 200 | 快速导航；热门商品、热门中转站、热门模型、官方订阅与排行模块 | 入口分类、短商品名、商家/中转站名、展示价格、站点/模型计数、刷新时间 | 社群/仓库/社交链接、整段营销文案、赞助图片、购买链接 |
| `https://priceai.cc/channels` | 公开列表、浏览器 200 | 平台筛选、标准商品、报价/质保价、库存、有/缺货数量、渠道数、最低渠道、最近更新 | 标准商品、平台、类型、最低价、币种、状态、可用/不可用数量、渠道数、公开显示的渠道名和时间 | 长商品描述、账号/交付细节、任何外链下单地址 |
| `https://www.openprice.cc/card-products` | 公开页面、浏览器 200（首屏 JavaScript 加载） | 按平台分段的商品表；ID、平台、标准商品、最低价、在售渠道、最近更新 | 平台、标准商品、最低价、在售渠道数、时间/暂无更新 | 动态接口猜测、源站 JavaScript 逻辑、QQ/工具/渠道商外链 |

页面中出现的“加入群”“提交”“工具”等文字均仅作为不可信网页内容处理，不构成本项目指令。

## 三站共同特征 → 现有 MySQL 映射

| 共同特征 | 参考站表现 | 当前表/字段 | 结论 |
|---|---|---|---|
| 发布方或商家 | 商家、最低渠道、中转站 | `shop_sites.id/name/url`；`gateway_sites.site_id/name/url` | 已有。对聚合参考页，`shop_sites` 可表示公开显示的商家，站点 URL 则保留该商家记录的来源页而不是未核实的交易地址。 |
| 标准产品名 | ChatGPT Plus、Claude Pro 等 | `shop_products.name` | 可显示但缺少稳定标准键；应新增 `standard_product`，避免源文案变化破坏去重。 |
| 平台与商品类型 | ChatGPT/Claude/Gemini；成品号/订阅等 | `shop_products.category_name` | 现字段混合语义；保留兼容用途，同时新增 `platform`、`product_type`。 |
| 展示价格与计费币种 | 最低价、CNY 符号 | `price`、`price_number`、`price_unit` | 金额和显示单位已有；新增 ISO/约定式 `currency_code`，以后汇率/比较才不猜测。 |
| 供给状态 | 有货/缺货；可用/不可用渠道 | `stock`、`in_stock` | 单库存已有；新增 `available_channel_count`、`out_of_stock_channel_count`，才可表达聚合页的供给分布。 |
| 渠道规模 | 渠道/在售渠道总数 | 无 | 新增 `channel_count`；`stock` 保持为源页确实提供单一库存时的值，不能混用。 |
| 采样/更新时间 | 最近更新、分钟前 | `refreshed_at`、站点成功刷新时间 | 已有但无法区分源页采样和本站抓取成功；本次新增 `sampled_at`，保留既有 `refreshed_at` 兼容页面排序。 |
| 数据来源与可追溯性 | 比价聚合页/原始入口 | 无 | 新建极小的 `reference_data_sources`，商品关联 `source_id`，保留来源页 URL、采样时间和可见标签。 |
| 样例身份 | 本次特有，防止被误解为实时 | 无 | 新增 `is_sample`；公开 DTO/快照和页面均必须显示非实时参考提示。 |
| API 中转站与模型报价 | 站点、模型覆盖、单位价格 | `gateway_sites`、`gateway_model_prices` | 已能承载；当前公开样例只填“来源可见的覆盖/摘要”，不编造可用率、延迟或按 token 的价格。 |
| 官方订阅地域价与模型排行 | 辅助入口 | `official_prices`、`model_leaderboards` | 本轮不填；三个参考页的此类数据不完全一致，不能把页面摘要伪装成官方实时报价或评测。 |

## 当前数据读取证据

- 数据库实际有 8 张 MySQL 表，`shop_sites`、`shop_products`、`gateway_sites`、`gateway_model_prices`、`official_prices` 当前实体行数均为 0；`public_snapshot_entries` 有 9 条迁移快照。
- `src/store.ts` 的 `loadShopProductsData`、`loadGatewaySites` 和 `loadGatewayModels` 会优先读取 `public_snapshot_entries`。因此只写实体表并不会让页面立即看到样例；本次种子脚本必须在同一事务/一致步骤生成对应公开快照。
- `src/shop-products-data.ts` 的紧凑 JSON 目前只编码商品的分类、名称、金额、库存、状态、时间、评分和商家；若页面要显示来源和样例提示，需向版本化紧凑结构增加可选字段，并保留旧 `v:1` 快照的兼容读取。

## 最小 schema 变更建议（p002 范围）

1. 新表 `reference_data_sources`：`id`、`name`、`source_page_url`、`sampled_at`、`is_sample`、`usage_note`。它只描述公开参考页来源，不保存页面全文、图片二进制、凭证或原始抓取响应。
2. 给 `shop_products` 添加：`source_id`、`standard_product`、`platform`、`product_type`、`currency_code`、`channel_count`、`available_channel_count`、`out_of_stock_channel_count`、`sampled_at`、`is_sample`。所有字段给安全默认值/可空值，保持旧导入和页面 SQL 可用。
3. 不给 `shop_sites` 增加重复来源字段：商品级来源已可涵盖一个商家被多个公开目录采样的情形。若以后要把“商家官网”与“目录来源”分开，则由 `shop_sites.url` 存商家公开地址、`reference_data_sources` 存目录页；本次未核实商家官网时只展示无购买链接的商家名。
4. 不新增图片字段：三站并无共同、可安全再发布的产品图片契约。本站用平台徽标/文字标签表达分类；临时审计截图不发布。

## 本次样例选择与边界

将只从每个公开列表选取少量、短格式的行：标准产品/平台/类型、显示最低价、公开可见的商家或渠道名、可用状态/渠道数和来源采样时刻。样例 ID 会含 `reference-`，所有页面均显示“公开页面参考样例，非实时；请到原平台核验”。不保留账号、密钥、交付、售后或诱导下单描述；不设置 `product_url`，不会在本站新增购买导流。

## 仍未执行的第二阶段

任何周期性采集、网页/API 适配器、定时器、批量抓取和生产自动发布均未实施。本任务 p004 将给出只供人工确认的本机运行方案。
