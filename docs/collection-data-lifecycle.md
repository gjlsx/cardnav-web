# AI LoveMoney 采集数据生命周期（当前规则）

日期：2026-08-29  
适用范围：本机 Python 采集器、`ailovemoney` MySQL、桌面总控台。本文取代旧文档中的 `raw -> staging -> 自动发布` 描述。

## 唯一数据流

```text
一个或多个来源选入同一 collection batch
  -> 记录来源原始响应（raw payload）
  -> 简单清洗，写项目统一格式的 collection_raw_records
  -> 人工点击或独立启用的定时 merge/import
  -> 合并、去重、整合后事务写入运行时实体表和 public snapshots
  -> 运行时表入库即是发布
```

采集和 merge/import 是两个独立步骤。采集、循环采集、fixture 测试、dry-run 均只写 raw；它们不得写运行时实体表或 `public_snapshot_entries`。不存在第二份“发布副本”或 SFTP/SQL 文件发布步骤：`merge_import_batch` 对运行时表及完整快照的一次 MySQL 事务就是发布。

## 程序写死、参数走 `catch.config`

采集程序、解析程序、merge/import 入库程序和它们的调用顺序写死：`PlaywrightCrawler` 只写 raw，独立 merge worker 只读 `raw_completed` batch 再入运行库/快照。不得再加第二条流水线、平行 schema 或 GUI 自有协议。

可变项只放在同一份 `scripts/crawlee_collection/catch.config`（仓库内模板为 `catch.config.example`）：采集哪些已登记来源、每项上限、重采 sleep/间隔、merge worker 是否启用及其轮询间隔。精确 allowlist URL 仍在代码里，配置不能增加任意 URL。所有 CLI、未来 GUI 按钮和 Linux 一键/systemd 都只调用同一套 CLI，并由该 CLI 读取这份配置；不要为 GUI 或服务器再复制一份参数。

中转站当前批准来源为 PriceAI 的精确模型目录 `https://priceai.cc/api-transit/models`、CardNav 的精确列表入口 `https://cardnav.xyz/llm-gateway`，以及 Hvoy AI 开源仓库的精确公开 JSON `https://raw.githubusercontent.com/hvoyai/awesome-ai-api/main/data.json`。CardNav 只可读取列表 DOM 已出现、且匹配同域 `/llm-gateway/<safe-slug>` 的一层详情页；不能访问详情中的外部“打开”链接、模型页、广告或其它路径。PriceAI 模型页只保存 raw payload 并提供本批次允许模型集合，不发布模型排行。Hvoy AI JSON 仅保存其原始 `rank`、站点名称、Hvoy 详情 URL、模型数/家族、可用率、延迟、用户评分/人数、支付/退款/发票等公开参考字段；其 `rank` 为来源参考位次，不是本站评分、模型能力或价格排名，Hvoy 详情 URL 不能被继续抓取。模型标准名为 trim、连续空白合并、Unicode casefold、空格替换为 `-`，例如 `GPT 5.6 Luna` -> `gpt-5.6-luna`；CardNav 详情中未命中该集合的模型不入运行库。一个详情页对应一个 `gateway_site` raw 稳定键，其白名单 `metadata_json` 可承载多个模型覆盖和公开价格；merge/import 在同一既有事务更新 `gateway_sites`、`gateway_model_coverage`、`gateway_model_prices` 及中转快照。来源可见评分只保留 raw，`site.score` 仍为展示初始值 50。

当前 MVP 的目标是本机 MySQL `ailovemoney`。采集器不在 `ai.lovemoney.live` 生产服务器运行。MVP 验收后，才可以单独批准把同一个 merge/import 事务切换到运行时服务器 MySQL；不得为远程目标创建第二种原始数据格式。

## 项目固定原始数据格式

`collection_raw_records` 是唯一的来源无关原始记录格式。它使用固定列/字段集合，兼容中转站、卡网商品、官方计划和模型排行；来源没有的字段必须为 `NULL`，不能补造值。来源原响应细节只存入 `collection_raw_payloads`，与统一 raw 记录通过 run/source 关联。

| 字段组 | 固定字段 | 用途 |
|---|---|---|
| 批次和来源 | `batch_id`, `run_id`, `source_id`, `source_class`, `source_priority`, `source_url`, `observed_at`, `collected_at`, `source_record_hash` | 审计、来源排序、变更定位 |
| 记录身份 | `record_kind`, `record_key`, `canonical_site`, `canonical_sku`, `plan_slug`, `country_code`, `task_slug`, `normalised_model` | 四种页面数据的稳定键 |
| 展示映射 | `site_name`, `platform`, `product_type`, `display_name`, `model_name`, `currency_code`, `price_text`, `price_number`, `supply_state` | 运行时表所需的共同业务字段 |
| 可选指标 | `channel_count`, `available_channel_count`, `out_of_stock_channel_count`, `price_unit`, `metadata_json` | 来源有值则写入，缺失保持 `NULL`；`metadata_json` 仅容纳白名单公开字段 |
| 处理状态 | `validation_state`, `validation_reason`, `manual_state`, `merged_at`, `imported_at` | 保留校验与人工状态，不改变原始来源事实 |

`collection_staging_observations` 保留为唯一旧 staging 表，供历史兼容和查看；新采集流程不向它双写，也绝不新增 `collection_staging_records`。

各表职责、采集写哪些、merge 写哪些见 [数据库说明](数据库说明.md)。

## 合并与入库规则

合并按同一 batch 的 `record_key` 分组：卡网为规范化站点域名 + canonical SKU；中转站为规范化站点域名；官方计划为 plan slug + 国家；模型排行为 task slug + 规范模型名。

1. 来源层级：本站公开 API > 本站公开 HTML > 聚合站；聚合站内部 PriceAI > CardNav > OpenPrice。
2. 每次合并先对每个 `stable key × source` 取最新有效 raw；只有其本机 `captured_at` 未超过 `RAW_FRESHNESS_HOURS=24` 的候选可参与合并。第三方页面的 `observed_at` 只用于展示采样时间，不用于新鲜度判断。
3. 高优先级来源在 24 小时内有有效字段时，低优先级不得覆盖；低优先级只可填补高优先级的空值。只有高优先级来源对该稳定键超过 24 小时没有有效 raw 时，新鲜的低优先级候选才可接管。
4. 同优先级的有效数字价格取最低价；无法解析的价格不参与最低价排序，但 raw 仍保留。
5. 当某个受影响稳定键的所有候选都超过 24 小时时，merge/import 标记 batch 已处理，但不删除、隐藏或改写既有运行时行和公开快照；页面继续显示既有最后采样时间。
6. `site.score` 只控制前端站点展示排序，当前初始值为 50，绝不参与来源合并。
7. 手工锁定或隐藏不阻止 raw 记录保存；它阻止对应 stable key 的 merge/import。取消标志后，可以重新执行 merge/import，不必重新抓取。

默认 `merge_import_enabled=false`。人工按钮可执行明确的 `merge_import_batch(batch_id)`；若未来开启定时 merge/import，必须调用同一事务服务并记录来源、批次、数量与结果。

## 独立 merge/import worker（已确认运行约束，尚未接入）

采集来源只负责把批准来源的响应和解析记录写入 raw。后续读取 raw、按稳定键合并/清洗并事务写入运行时库/快照，统一由一个本机独立 worker 负责；它不承担网页采集。

- worker 默认关闭，只有人工或明确配置后才能运行；不在生产服务器运行。
- 同一时刻只能有一个 worker 实例和一条执行线程。它以 10 秒间隔轮询，串行挑选一个 `raw_completed` batch，调用既有 `merge_import_batch(batch_id)` 完成后才处理下一个 batch。
- worker 沿用本节全部合并规则：手工闸门、来源优先级、同级最低价和本机 `captured_at` 24 小时新鲜度。成功后的 batch 保持幂等；候选均过期仍标记已处理，但不删除或隐藏当前运行时数据。
- 该约束只定义 merge/import 的运行位置与串行度；不改变来源审批、allowlist、raw 审计格式、生产发布或远程 MySQL 的边界。

## 安全与数据边界

- 未批准或 allowlist 不明确的来源只能使用 fixture，不能发 HTTP。
- 不存 Cookie、账号、验证码、订单、交付/售后内容、密码、Token 或私钥。
- 白名单公开响应可在本机 raw payload 审计表保留 30 天；解析后的统一 raw 记录及运行审计按保留策略保存。
- 生产发布、备份、恢复仍由合作运维 Tab 的独立双确认流程处理，不能和数据 merge/import 混为一件事。
