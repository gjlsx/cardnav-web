# 独立 Crawlee 浏览器采集器

这是新采集正式路径：仅使用 Crawlee for Python 的 PlaywrightCrawler。已登记来源包括 PriceAI 三个原有公开入口、PriceAI 中转标准模型页，以及 CardNav 中转站列表和其列表直接发现的同域一层详情页。来源登记在 `sources.py`，页面解析在 `parser.py` / `gateway.py`，MySQL 复用门面在 `database.py`，默认关闭的 merge/import worker 在 `worker.py`，CLI 在 `cli.py`。

```powershell
python -m scripts.crawlee_collection check-config
python -m scripts.crawlee_collection list-sources
python -m scripts.crawlee_collection collect --source priceai-card-subscriptions
python -m scripts.crawlee_collection collect --source priceai-card-subscriptions --loop
python -m scripts.crawlee_collection collect --all
python -m scripts.crawlee_collection list-raw
python -m scripts.crawlee_collection merge-once --source priceai-card-subscriptions
python -m scripts.crawlee_collection worker --source priceai-card-subscriptions --loop
python -m scripts.crawlee_collection.gui
```

`collect` 只经 Crawlee `PlaywrightCrawler` 访问来源登记中的精确 URL，浏览器并发固定为 1，结果只写 raw。`worker` 默认不运行。

中转站采集会先读取 `https://priceai.cc/api-transit/models` 建立本批次唯一标准模型集合；模型名执行 trim、连续空白合并、casefold、空格替换为 `-`，例如 `GPT 5.6 Luna` 为 `gpt-5.6-luna`。随后从 `https://cardnav.xyz/llm-gateway` 的已渲染列表只发现 `https://cardnav.xyz/llm-gateway/<slug>` 同域详情页；不访问详情页“打开”的外部站点或模型页。仅详情中命中 PriceAI 标准模型集合的覆盖和公开价格会进入 raw，再由 merge/import 写既有中转运行表和快照。

采集/解析/merge 程序和调用顺序写死。采集几项、重采 sleep、merge 轮询等可变项只来自本目录 `catch.config`（复制 `catch.config.example`）。所有 CLI 子命令读同一份文件；GUI 或 Linux 一键也只能调这些 CLI，不得另写参数。配置只能启用 `sources.py` 已登记来源，不能增加任意 URL。不要把旧 `scripts/collection/sources.json` 导出进 `catch.config`。

新 GUI 两个模块 Tab：采集、入库。停止按钮统一为「停止卡网 / 停止官方 / 停止中转」。每页独立日志，全部 `subprocess` 上述 CLI。网站启动不放在此窗口。旧 `python scripts/collection/gui.py` 仍是 legacy 总控台，不启动本程序。

它不访问下游商户链接，也不处理登录、验证码、CAPTCHA、挑战页或访问控制绕过。`scripts/collection/` 保留作历史 legacy，不由本目录入口调用。
