# AI LoveMoney 数据导航与采集边界（当前事实）

日期：2026-08-28  
范围：`tasklist08281547` 已确认决策。本文给后续 AI / 发布者使用；冲突时以本文和仓库代码为准，不以旧头脑风暴为授权。

## 公开站点事实

- 站点：`https://ai.lovemoney.live/`
- 运行时：Astro 7 SSR + Node standalone，`127.0.0.1:3101`
- Apache `*:80` / `*:443` 只服务 `ai.lovemoney.live`
- 数据库：MySQL/MariaDB `ailovemoney`；公开页优先读 `public_snapshot_entries`
- LikeShop 只走 `8086` / `8090` / `8095`，不占用 80
- 生产站只读展示，不运行采集器或调度器

路由保持不变，只改导航显示名：

| 路由 | 中文导航 | English | Русский |
|---|---|---|---|
| `/llm-gateway` | 中转网站 | Gateway sites | Сайты-шлюзы |
| `/official-price` | 官方网站 | Official sites | Официальные сайты |
| `/guide` | 帮助 | Help | Помощь |
| `/shops` | 卡网商品 | Card shops | Карточные магазины |
| `/model-leaderboard` | 模型排行榜 | Model leaderboard | Рейтинг моделей |

## 本轮已实现（可手工验证）

- `/shops` 默认按权威 SKU 聚合：一行一个 `catalog_products.slug`，同站去重后按来源 `priority` 取有效字段，同优先级取最低价；`site.score` 展示初值为 50，来源没有 score。
- 模型 / 官方计划可跳到内部结果：`/shops?target=`、`/llm-gateway?model=`。无声明关系时显示空态，不猜测映射。
- `/llm-gateway`、`/official-price`、`/model-leaderboard` 有公开参考样例；样例无购买外链。
- 模型分类：`coding`、`creative-writing`、`math`、`text-to-image`、`video-generation`。视频生成有标签和数据结构，当前无核验样例，显示「暂无公开参考样例」。
- 现有 `/partnership` 与商家/中转站提交入口继续可用；提交结果不自动联网、不自动写入公开快照。

种子：

```bash
pnpm run seed:reference-samples
```

只刷新样例实体行和对应公开快照，不覆盖 `popular-search-terms`。

## 采集分层

采集层保存比展示层更详细的白名单字段；公开 DTO 继续紧凑。

合并优先级（同一规范化目标站）：

1. 该站自己的 API
2. 该站公开网页
3. 聚合站：PriceAI > CardNav > OpenPrice

规则：按规范化站名去重；高优先级覆盖有效字段，低优先级只补空；同优先级选最低价。`site.score=50` 属于网站展示初值，来源配置不得覆盖。

来源配置默认值：`enabled=false`、`interval_minutes=60`、`max_items_per_run=1000`；`0` 表示不限条数。批准状态默认 `draft`。未批准来源只跑 fixture；已批准且 allowlist 明确的来源可真实 HTTP 写入**本机** MySQL 的统一 raw 表。后续 merge/import 才按稳定键和本节优先级写运行时表/快照；该入库即发布。本机总控台：`python scripts/collection/gui.py`。

## 已批准的本机总控台方向（p011–p019）

仍禁止：未批准来源联网、在 `ai.lovemoney.live` 上跑采集器、MVP 本机直连远程 MySQL。定时采集和定时 merge/import 均默认关闭，必须分别启用。

已批准、公开且字段白名单明确的来源可由本机 GUI 手工真实 HTTP 采集，保存来源 raw payload 与带来源标签的统一 `collection_raw_records`；来源字段缺失时保持 `NULL`。新采集不再把数据双写进 staging 或自动写正式表。人工或独立启用的定时 `merge_import_batch` 才对 raw 按稳定键、来源优先级、同级最低价整合，并在一个事务写入运行时实体表/快照；写入即发布。来源仍默认 `enabled=false`，`interval_minutes=60`、`max_items_per_run=1000`；人工运行忽略 enabled 但不忽略上限。原始公开响应保留 30 天，解析记录和审计长期保留；账号、Cookie、验证码、订单和交付数据均不得保存。

站点级手工覆盖/隐藏按稳定键在 merge/import 阶段生效：批量来源响应与统一 raw 均继续保存，覆盖记录不覆盖运行时展示。解除覆盖后可重新 merge/import；不恢复旧快照。`collection_staging_observations` 仅保留作唯一历史兼容/查看 staging 表。MVP 只管理本机 MySQL；远程 MySQL 的本机直连读写属于 MVP 后另行批准的任务。服务器发布经合作运维 Tab 的二次确认后，遵循项目根目录 `howtorunvpsnew.md` 真执行，并保持 LikeShop 8086/8090/8095 不受影响。

当前唯一采集生命周期与字段合同见 [collection-data-lifecycle.md](collection-data-lifecycle.md)。

## 秘密边界

密码、SSH 私钥、token、cookie、数据库连接串、SQL dump、完整第三方 HTML 不得写入 git、tasklog 或 README。仅允许白名单公开响应在本机 MySQL raw 审计表保存 30 天；连接方式只引用本机受控安全文件。
