# 独立 Crawlee 浏览器采集器

这是新采集正式路径：仅使用 Crawlee for Python 的 PlaywrightCrawler。已登记六个来源项：PriceAI 三个原有公开入口、PriceAI 中转标准模型页、CardNav 中转站列表/同域一层详情，以及 Hvoy GitHub 公开 JSON。来源登记在 `sources.py`，页面解析在 `parser.py` / `gateway.py`，MySQL 复用门面在 `database.py`，默认不自动启动的 merge/import worker 在 `worker.py`，CLI 在 `cli.py`。本文于 2026-09-07 按源码核对；[当前边界](../../docs/data-nav-and-collection.md)、[数据生命周期](../../docs/collection-data-lifecycle.md) 优先于历史引擎对照记录。

以下先列只读配置检查，再列需要明确操作授权的采集/入库命令；不要整段复制执行。

```powershell
python -m scripts.crawlee_collection check-config
python -m scripts.crawlee_collection list-sources
python -m scripts.crawlee_collection collect --source priceai-card-subscriptions
python -m scripts.crawlee_collection collect --source priceai-card-subscriptions --loop
python -m scripts.crawlee_collection collect --all
python -m scripts.crawlee_collection list-raw
python -m scripts.crawlee_collection merge-once --source priceai-card-subscriptions
python -m scripts.crawlee_collection worker --source priceai-card-subscriptions --loop
```

`collect` 只经 Crawlee `PlaywrightCrawler` 访问来源登记中的精确 URL，浏览器并发固定为 1，结果只写 raw。`worker` 默认不自动运行；配置 enabled=false 不阻止显式 CLI `collect`、`--loop`、`merge-once` 或 `worker --loop`。不要把默认关闭误认为手工操作安全锁，也不要并行启动多个入库进程：当前 worker 类内单例不是跨进程互斥。

Hvoy 只读取 `https://raw.githubusercontent.com/hvoyai/awesome-ai-api/main/data.json`，不继续抓详情或外部商户；`rank`、在线率、延迟与用户评分为上游中转参考，不是本站综合评分或模型价格。模板 `collect.source_ids` 有五个任务项；CardNav 任务内部会先抓 PriceAI 标准模型页，所以 registry 六项与任务五项不矛盾。实际任务以本机配置为准。

中转站采集会先读取 `https://priceai.cc/api-transit/models` 建立本批次唯一标准模型集合；模型名执行 trim、连续空白合并、casefold、空格替换为 `-`，例如 `GPT 5.6 Luna` 为 `gpt-5.6-luna`。随后从 `https://cardnav.xyz/llm-gateway` 的已渲染列表只发现 `https://cardnav.xyz/llm-gateway/<slug>` 同域详情页；不访问详情页“打开”的外部站点或模型页。仅详情中命中 PriceAI 标准模型集合的覆盖和公开价格会进入 raw，再由 merge/import 写既有中转运行表和快照。

采集/解析/merge 程序和调用顺序写死。采集几项、重采 sleep、merge 轮询等可变项只来自本目录 `catch.config`（复制 `catch.config.example`）。所有 CLI 子命令读同一份文件；GUI 或 Linux 一键也只能调这些 CLI，不得另写参数。配置只能启用 `sources.py` 已登记来源，不能增加任意 URL。不要把旧 `scripts/collection/sources.json` 导出进 `catch.config`。

配置键：`collect.source_ids`、`collect.max_items_per_run`、`collect.interval_seconds`；Hvoy 独立 `collect.source_settings.hvoyai-awesome-ai-api.interval_minutes` 模板为 480 分钟；`merge.poll_interval_seconds` 模板为 10 秒，`merge.connection_idle_ttl_s` 为连接空闲策略。`collect.enabled`、Hvoy `enabled` 和 `merge.enabled` 模板均为 false，不自动安装调度。

新版 GUI 本机文件 `gui.py` 尚未跟踪，新检出不要假定存在。已有此文件时可用 `python -m scripts.crawlee_collection.gui`：采集/入库两个模块、独立日志，经 subprocess 调用同一 CLI。旧 `python scripts/collection/gui.py` 仍是 legacy 总控台，不启动本程序。

当前人工运营节奏为每天一次：在本机 GUI 或同一 CLI 中只运行所选已批准模块，核对 raw 结果后才显式执行对应 batch 的 merge/import。它不是 `--loop`、计划任务或生产调度授权；不得并行启动 worker 或入库命令。

它不访问下游商户链接，也不处理登录、验证码、CAPTCHA、挑战页或访问控制绕过。`scripts/collection/` 的旧采集入口保留但不调用；本目录仍复用其 `collection_lib` 的合同、raw/merge 事务等基础服务，不能把整个目录删除。
