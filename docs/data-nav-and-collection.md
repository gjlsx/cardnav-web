# AIGATE 数据导航与采集边界

核对日期：2026-09-07。当前技术边界以本文与源码为准；业务方向见 [PRODUCT_STRATEGY](PRODUCT_STRATEGY.md)，验收顺序见 [ROADMAP](ROADMAP.md)，运行与验证状态见 [CURRENT_STATUS](CURRENT_STATUS.md)。历史设计不是当前执行授权。

## 公开站点与导航

- 当前品牌/主域为 AIGATE / `https://aigate.live/`；旧 `ai.lovemoney.live` 保留路径和查询参数并转向新域。9 月 3 日发布 QA 记录旧域 HTTP/HTTPS 308 与新域浏览器结果；本轮未访问生产站。
- Astro SSR + Node standalone，本机与服务器 Node 入口为 `127.0.0.1:3101`；MySQL/MariaDB `ailovemoney`，公开页读取 runtime 表和 `public_snapshot_entries`。
- Apache 80/443 承接 AIGATE 与旧域兼容；LikeShop 保持 8086/8090/8095 隔离，不改其 vhost。
- 代码支持 zh/en/ru，公共布局均提供语言入口。优先建设中文再扩英文是经营顺序，不是“俄语不可用”。本轮未复跑三语浏览器验收。

| 路由 | 中文导航 | English | 当前用途 |
|---|---|---|---|
| `/llm-gateway` | 中转网站 | Gateway sites | 站点列表、模型覆盖与可比价格，详情及站内关联 |
| `/official-price` | 官方网站 | Official sites | 官方计划参考与内部关联 |
| `/guide` | 帮助 | Help | 使用路径、准备条件及风险说明 |
| `/shops` | 卡网商品 | AI shops | 标准 SKU 聚合，同站去重与来源参考 |
| `/model-leaderboard` | 排名参考 | Ranking reference | 模型表现、中转参考、价格参考；保留旧路由兼容 |

模型/计划可关联到 `/shops?target=` 或 `/llm-gateway?model=`，没有声明关系则显示空态。提交/合作入口不会因此自动获准采集或写入公开快照。上游 Hvoy rank、上游可见评分、初始 `site.score=50` 和未来本站综合评分不得混称；商业/自然榜分离的完整产品验收仍属于 M1。

## 当前采集入口与合同

正式入口为 [Crawlee CLI](../scripts/crawlee_collection/README.md)，仅通过 Crawlee + Playwright 采集精确已登记来源，并发固定 1。新版 `scripts/crawlee_collection/gui.py` 当前为本机未跟踪文件，不能当作新检出已包含的能力；`scripts/collection/gui.py` 是保留的 legacy 总控台，不作为新采集入口。

唯一数据流：已批准来源 -> 本机 raw payload / `collection_raw_records` -> 显式独立 merge/import -> runtime 表 / public snapshots。采集本身不写运行库；独立入库事务才更新其目标数据库的公开读数据。生产站不运行采集器/定时器，也不通过公开浏览器路由采集或写采集数据。

- 来源/URL 登记在 `scripts/crawlee_collection/sources.py`；现有六个 registry 项包括 PriceAI 四个入口、CardNav 列表/一层详情与 Hvoy GitHub JSON。登记数不是 `collect --all` 的配置任务数；CardNav 任务会先读取 PriceAI 标准模型目录。
- 配置仅用 `scripts/crawlee_collection/catch.config`；缺少本机文件时读取模板。程序与顺序写死，不能在配置添加任意 URL。具体键和手工命令边界见采集 README。
- merge/import worker 已接入，默认不自动启动；串行处理 `raw_completed` 批次，只读 raw，不采集网页。轮询间隔来自 `merge.poll_interval_seconds`，模板为 10 秒。
- 调度 enabled 默认关闭不是手工 CLI 安全锁；显式 `collect`、`--loop`、`merge-once`、`worker --loop` 会执行相应操作，不得在文档验证时随手运行。
- 新鲜度、来源优先级、同级最低可比价和手工锁/隐藏规则见 [数据生命周期](collection-data-lifecycle.md)。raw 保留事实，手工闸门作用于 merge/import；来源故障不清空运行数据。

[旧采集引擎对照记录](collection-capture-engine.md) 保留八月选择过程及本机笔记；其中“尚未接入”或按需 HttpCrawler 的历史设想，不覆盖现行 Playwright CLI。禁止重新启用旧采集入口、增加第二 schema 或平行 staging 流水线。

## 数据与部署分界

当前 CLI 以本机 `.env` 的 `MYSQL_*` 为目标，禁止把本机直连远程数据库当作默认采集链路。获批远程数据库管理是独立运维能力，不等于采集自动获准远程写库。

本机 merge/import 与 VPS 发布是两种操作：前者更新本机运行库/快照，后者按 [发布指南](../howtorunvpsnew.md) 备份远程、上传构建并导入本机运行数据。文档整合不授权二者执行，发布也不能部署采集器。

`pnpm run seed:reference-samples` 仅用于明确批准的隔离样例数据库；会写实体和公开快照，不得作为现有真实数据的启动/发布前置步骤。九月三日发布证据见 [QA](../taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p003.md)，不以八月样例清单代表当前库存。

## 敏感数据与扩张

只采明确白名单的公开字段；不跟随商家外链，不登录、不处理 CAPTCHA、不绕过访问控制。需求队列可以提出新来源，不能自动扩张 allowlist。

密码、密钥、Token、Cookie、连接串、SQL dump 和完整第三方响应不得进入 Git/日志/README。公开 raw 响应仅保留在受控本机审计存储，按既有生命周期管理。新增商家 Feed、自营域名和商业归因必须在后续任务明确主体、授权、目的和字段；不能从本轮战略推定具体站点所有权。
