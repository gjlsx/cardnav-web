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

## 合并与入库规则

合并按同一 batch 的 `record_key` 分组：卡网为规范化站点域名 + canonical SKU；中转站为规范化站点域名；官方计划为 plan slug + 国家；模型排行为 task slug + 规范模型名。

1. 来源层级：本站公开 API > 本站公开 HTML > 聚合站；聚合站内部 PriceAI > CardNav > OpenPrice。
2. 高优先级的有效字段不能被低优先级覆盖；低优先级只可填补高优先级的空值。
3. 同优先级的有效数字价格取最低价；无法解析的价格不参与最低价排序，但 raw 仍保留。
4. `site.score` 只控制前端站点展示排序，当前初始值为 50，绝不参与来源合并。
5. 手工锁定或隐藏不阻止 raw 记录保存；它阻止对应 stable key 的 merge/import。取消标志后，可以重新执行 merge/import，不必重新抓取。

默认 `merge_import_enabled=false`。人工按钮可执行明确的 `merge_import_batch(batch_id)`；若未来开启定时 merge/import，必须调用同一事务服务并记录来源、批次、数量与结果。

## 安全与数据边界

- 未批准或 allowlist 不明确的来源只能使用 fixture，不能发 HTTP。
- 不存 Cookie、账号、验证码、订单、交付/售后内容、密码、Token 或私钥。
- 白名单公开响应可在本机 raw payload 审计表保留 30 天；解析后的统一 raw 记录及运行审计按保留策略保存。
- 生产发布、备份、恢复仍由合作运维 Tab 的独立双确认流程处理，不能和数据 merge/import 混为一件事。
