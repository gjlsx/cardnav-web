# 采集引擎选择与本机对照记录

日期：2026-08-29  
状态：已确认后续适配器选择；尚未新增或启用真实来源。

## 决策

后续获批准来源的采集适配器首选 **Crawlee for Python**：公开、已 allowlist 的静态响应使用 `HttpCrawler`；只有页面确实需要执行 JavaScript、且不涉及登录、验证码或访问控制时，才使用 `PlaywrightCrawler`。所有响应仍先进入项目既有 raw 批次，独立 merge/import worker 再处理 raw；采集框架不得直接写运行时库。

选择理由是本项目只有少量、异构的公开来源，而 raw 保存、合并和发布事务已经由本项目实现。Crawlee 能让每个来源保持一个小型适配器，并在同一 Python 异步模型下按需选择 HTTP 或浏览器渲染。正式接入时 worker 的采集并发上限必须为 1，以满足已确认的单例、单线程、串行处理约束。

`curl_cffi` 不用于 TLS/浏览器指纹伪装或规避防护；Scrapy 不作为本项目新增来源的默认引擎。若未来需求变成大规模、深层链接爬取，再单独评估 Scrapy 的调度、重试和限速优势。

## 2026-08-29 重跑事实

在 `D:\work\dock\testcatch\benchmark.py` 中，仅运行三套 HTTP 获取与挑战页识别，不运行验证码滑块脚本，也不写回结果文件：

| 项目 | 结果 |
|---|---|
| PriceAI 公开产品页 | 三套 HTTP 客户端均得到 HTTP 200，页面文本包含 30 次 `sourceStoreName`。单独 RSC 正则试验识别出 29 个 `id + URL` 片段，说明“30 次字符串”不是已解析的 30 条规范报价。 |
| 下游 LDXP 商品页 | 三套 HTTP 客户端均得到 HTTP 200，但响应被识别为挑战页；HTTP 200 不等于取得商品数据。该来源不具备可采资格。 |
| 本次总耗时 | curl_cffi 2.900 秒、Crawlee 1.889 秒、Scrapy 3.126 秒。它们包含启动、两次网络请求、解析与日志开销，只是一次观察，不是吞吐或稳定性排名。 |

## 为什么原始评分不能作为结论

- Crawlee 和 Scrapy 的单站 `time_sec` 在原始结果 JSON 中均为 `0`；脚本根本没有为它们计时。
- 脚本实际只实例化 `HttpCrawler`，从未执行 `PlaywrightCrawler`；因此不能把“能无缝通过 JS/滑块”写成实测能力。
- `score_card` 的数值是源码中预设常量，不是由测试计算得出；而且只运行一次、没有预热、重复样本、失败率或解析正确性断言。
- `sourceStoreName` 字符串计数不能替代 schema 校验、去重、价格/库存字段提取和 raw 落库检查。
- `test_ldxp_slider.py` 包含 `navigator.webdriver` 隐藏和拖动人机验证滑块的代码。它不属于项目允许的采集能力，不能运行、集成或作为测试证据。
- 现有基准将 Scrapy 配为 `ROBOTSTXT_OBEY=False`；正式来源适配器必须遵守来源审批、allowlist、站点规则及项目数据边界。

## 正式接入前的最小验收

对每个拟批准来源建立 fixture 和适配器测试，至少验证：允许 URL、状态/内容类型、确定的字段 schema、稳定键、重复记录去重、raw payload/record 审计、无 Cookie/验证码等敏感字段写入、以及失败时不触发 merge/import。浏览器回退只验证公开可渲染内容，不尝试绕过挑战、验证码或登录。
