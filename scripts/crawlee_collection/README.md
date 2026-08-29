# 独立 Crawlee 浏览器采集器

这是新采集正式路径：仅使用 Crawlee for Python 的 PlaywrightCrawler，且当前仅有 PriceAI 三个精确公开入口。来源登记在 `sources.py`，页面解析在 `parser.py`，MySQL 复用门面在 `database.py`，默认关闭的 merge/import worker 在 `worker.py`。

它不访问下游商户链接，也不处理登录、验证码、CAPTCHA、挑战页或访问控制绕过。`scripts/collection/` 保留作历史 legacy，不由本目录入口调用。
