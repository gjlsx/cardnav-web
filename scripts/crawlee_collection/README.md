# 独立 Crawlee 浏览器采集器

这是新采集正式路径：仅使用 Crawlee for Python 的 PlaywrightCrawler，且当前仅有 PriceAI 三个精确公开入口。它的来源登记、页面解析、MySQL 持久化、worker 和 CLI 将位于本目录。

它不访问下游商户链接，也不处理登录、验证码、CAPTCHA、挑战页或访问控制绕过。`scripts/collection/` 保留作历史 legacy，不由本目录入口调用。
