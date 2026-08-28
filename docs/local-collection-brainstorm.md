# 本机自动采集与发布方案（头脑风暴，待确认，不实施）

## 本文状态

这是采集方案的设计输入，**不是授权**，也不是可直接投入生产的采集器。当前事实与已实现边界见 [data-nav-and-collection.md](data-nav-and-collection.md)。`tasklist08281547.p006` 只允许本机 CLI/GUI、fixture/dry-run 和 MySQL staging 演练；默认 `enabled=false`。没有来源批准时不得发 HTTP，不得安装计划任务，不得自动 publish。

本轮样例已经证明的数据结构是：**标准产品 × 商家/渠道 × 来源页 × 采样时点**。任何未来自动化必须以此为中心，而不是仅“抓网页文字”。

## 1. 先定义来源清单，而不是先写通用爬虫

每一个来源必须是数据库/配置中一条显式登记项；默认拒绝未知域名。首批可分为三类：

| 类别 | 候选数据 | 采集优先方式 | 主要风险 | 初次批准要求 |
|---|---|---|---|---|
| API 中转站 | 站名、公开模型、公开价格/计费单位、公告 | 提供方许可的 API 或公开价格页 | 价格单位不一、服务状态难以验证、接口条款 | 每站单独确认 API/页面允许范围、模型字段和频率 |
| 商业小店/渠道商 | 标准产品、展示价、库存/状态、公开更新时间 | 店方明确提供的公开目录/API；没有许可则不采 | 登录、反爬、个人信息、交付/账号类敏感描述 | 商店书面/明确授权或条款允许；限定字段白名单 |
| 公开聚合比价页 | 标准产品、聚合最低价、渠道数、时间 | 公开页的许可字段或对方公开导出 | 聚合站本身的条款、二次分发、陈旧价格 | robots/条款/联系方式审查，最好取得合作/导出许可 |

`cardnav.xyz`、PriceAI、OpenPrice 在本轮仅是少量公开**参考样例**来源，不能自动进入抓取名单。要采集其中任何一个，仍需要逐站审批。

每条来源登记的最小内容：`source_id`、主体/联系人、根域名、允许 URL/接口、允许字段、允许频率、robots/条款检查日期、授权证据位置（仅内部、不可公开）、数据保留期、负责人、停用开关。没有完整登记项时 CLI 必须报错退出。

## 2. 推荐的本机架构

```text
已审批 source registry
       │（仅 allowlist）
       ▼
本机 collect CLI --dry-run / --source <id>
       │  限速、robots/条款门禁、适配器
       ▼
staging JSONL / 受限 MySQL staging
       │  标准化、去重、异常检查、人工批准
       ▼
实体表（shop_* / gateway_*）+ provenance/run 记录
       │  单事务生成版本化 public_snapshot_entries
       ▼
AI LoveMoney 只读页面（显示来源、采样时间、非实时提示）
```

关键原则：采集、审核和公开发布是三个独立阶段。定时器只能运行 collect/dry-run；它**不能**直接覆盖公开快照或生产数据库。上线发布必须通过明确的审核命令/任务和事务化快照切换。

## 3. 建议的未来目录与命令边界

批准后再创建，当前不创建：

```text
scripts/collection/
  collect.ts                # 明确 source 参数；默认 --dry-run
  validate.ts               # 不联网，只验证 staging
  publish.ts                # 需审批 token/交互确认；仅处理已批准 run
  adapters/
    gateway-<source>.ts
    merchant-<source>.ts
    aggregate-<source>.ts
  source-registry.json      # allowlist，不存秘密或登录态
```

建议的调用意图（示意，尚不可运行）：

1. `collect --source approved-x --dry-run`：读取一个批准来源，写本机 staging，不写公开表。
2. `validate --run <id>`：检查 schema、标准化、异常价、重复和字段许可，生成审核报告。
3. 人工审阅样例差异与报告；仅通过的 run 才进入下一步。
4. `publish --run <id> --approved-by <human>`：在 MySQL 事务内写实体表、provenance 和对应 `public_snapshot_entries`；失败时完全回滚。
5. 发布后浏览器检查 `/shops`、`/llm-gateway` 和数据计数；失败时切回上一版快照而不是重新抓取。

本机 `.env` 仅放数据库/可获许可 API 的秘密；URL allowlist、频率、字段名单和开关放可审阅的非秘密配置。日志不得打印 Authorization、Cookie、帐号、商品敏感描述或完整 HTML。

## 4. 适配器契约

不要以“一个万能 CSS selector 爬虫”开始。每个已批准来源一个小适配器，返回同一中间对象：

```ts
type CollectedOffer = {
  sourceId: string;
  sourcePageUrl: string;
  observedAt: string;
  standardProduct: string;
  platform: string;
  productType: string;
  displayName: string;
  priceText: string | null;
  priceNumber: number | null;
  currencyCode: string | null;
  supplyState: 'in_stock' | 'out_of_stock' | 'unknown';
  channelCount: number | null;
  availableChannelCount: number | null;
  outOfStockChannelCount: number | null;
  merchantDisplayName: string | null;
  evidence: { selectorOrField: string; valueHash: string }[];
};
```

- **API 中转站**：优先文档化 API；记录模型 ID、模型族、输入/输出/缓存价格、单位、币种、公开发布时间。没有可信计费单位时不写价格，不能拿可用率或延迟做猜测。
- **商业小店**：只取已授权的公开目录字段；禁止登录、验证码、购物车、下单、个人资料、订单、帐密、交付说明和站内搜索的批量枚举。
- **聚合页**：取其展示的聚合指标，`merchantDisplayName` 与 source 分开；不能伪称已核验的原商家价格。
- **图片**：默认不抓取、不下载、不转存。未来仅在来源明确授权再发布时，保存许可记录、原 URL、hash、尺寸和过期时间；否则本站继续使用文字/平台徽标，不使用第三方商品图或整页截图。

## 5. 标准化、质量门槛和数据库演进

现有 `reference_data_sources` 与 `shop_products` 的 `source_id`、`standard_product`、`platform`、`product_type`、`currency_code`、渠道计数、`sampled_at`、`is_sample` 已能承载本次样例。自动化前建议**另开审批任务**，补充以下运行审计表，而不是把原始页面塞进 `public_snapshot_entries`：

| 表/记录 | 用途 | 不应保存 |
|---|---|---|
| `collection_sources` | 批准后的来源规则、allowlist、频率、状态、授权复核时间 | 秘密、Cookie、原始凭证 |
| `collection_runs` | 开始/结束、版本、字段数、成功/失败、人工批准人、摘要 hash | 完整原始 HTML、个人资料 |
| `collection_staging_offers` | 受控的中间标准化结果、run ID、质量状态、来源 URL | 登录内容、交易/交付敏感详情 |
| `collection_anomalies` | 单位变化、异常价格、结构变化、去重冲突 | 不必要原文 |

质量规则建议：

- 标准产品由受控词典映射（如 `chatgpt-plus`、`claude-pro`），未知值进入人工审核，不自动新建。
- 货币/单位解析失败时保留 `price_text`，`price_number=null`，不参与最低价排序。
- 同 `source_id + standard_product + merchant + observed window` 仅留一个候选；保留来源 hash 以定位变动。
- 新价相对最近已批准价变化超过阈值、渠道数突然归零、关键 selector/API 字段消失时，标注 anomaly，停止该来源发布。
- 将 `observed_at`（来源可见时间）、`collected_at`（本机请求完成）和 `published_at`（公开快照切换）严格分开。
- `public_snapshot_entries` 使用一个 run/version 原子生成；网页永远读取完整成功快照，不能读取半抓取结果。

## 6. 频率、限速和本机定时建议

建议从低频、单来源、人工发布开始：

| 阶段 | 频率上限 | 并发 | 发布方式 | 目标 |
|---|---:|---:|---|---|
| 试点 | 人工触发 | 1 | 人工审核后发布 | 验证字段、条款、页面稳定性 |
| 已批准公开价格/API | 6–12 小时一次（以来源允许值为准） | 每域名 1 | 审核队列 | 验证时间/价格变化 |
| 已合作且明确授权的来源 | 不快于合同/文档限制 | 每域名 1–2 | 双人/规则批准 | 稳定的常规更新 |

本机 Windows Task Scheduler 的未来设置：

- 只调度 `collect --source <approved> --dry-run`，用专用低权限 Windows 账户运行，工作目录固定到仓库，日志定向到用户运行目录而非 Git 仓库。
- 任务间隔需大于单次最长时间；禁用“并行启动新实例”；失败最多重试一次并采用指数退避。
- 用一个人工可见的结果报告/通知提示“待审核 run”，而不是自动发到生产。
- 限制网络到 allowlist；不上网时或数据库不可用时直接失败，不使用旧 Cookie/缓存绕过。
- 任务计划、凭证、环境文件的创建必须由用户在后续任务明确批准后才执行。

服务器端不应成为采集器。服务器只接收已审核的最小导入/发布结果，继续提供只读网站；这符合当前“本地脚本跑”的要求，也避免生产 IP 对来源站形成额外访问负担。

## 7. 可观测性、人工处置与回滚

每次 run 至少记录：来源 ID、开始/结束、请求数量、响应类别汇总、解析/通过/拒绝条数、速率、版本、异常数、人工审批状态。告警条件：连续失败、robots/条款状态过期、结构字段消失、异常价格、数据量骤降、发布快照与实体表计数不一致。

人工处置顺序：停用来源 → 保留最后已批准快照 → 审核异常和授权 → 修复适配器/规则 → 再次 dry-run → 审核 → 发布。回滚是恢复上一份完整公开快照/已批准 run，而不是删除数据库或重新向源站请求。

## 8. 需要用户确认的决定

在任何自动化实现前，请确认：

1. 首批**明确授权**的数据来源名单，以及每个来源的 URL/API allowlist。
2. 是否已有书面授权，或是否允许把 robots/条款审查结果作为批准前置条件；没有则该站不实现。
3. 可采字段白名单：是否只收标准产品、价格、供给、来源、时间，明确排除帐号、验证码、交付与售后描述。
4. 每站最大频率、时段、并发和数据保存期限。
5. 是否接受“自动 collect + 人工 publish”的安全默认，还是哪些已合作来源可在规则通过后自动发布。
6. 价格异常阈值、未知商品/币种的处理和人工审核人。
7. Windows 本机计划任务的运行账户、告警方式和日志保存位置。
8. 生产导入方式：继续通过本地审核后导出最小 SQL/数据包上传，还是在受控 SSH tunnel 下从本机执行发布。

## 9. 批准后的第一个小 TaskExec 建议

不要一口气做多来源爬虫。建议先建一个独立 tasklist，只含以下 P0：

1. `p001`：用户提供一个已授权来源的书面范围，建立 `collection_sources` + source registry（无网络请求）。
2. `p002`：只为该来源实现 `collect --dry-run`，1 页/1 个许可 API，最多 10 条结果写入 staging，加入限速/脱敏/fixture 测试。
3. `p003`：实施 validate/anomaly/人工报告；仍不写公开快照。
4. `p004`：用户查看差异后，单独批准一次 staging → public snapshot 的事务发布和浏览器验证。
5. `p005`：仅在上述稳定后，讨论 Windows Task Scheduler；先默认每天一次 dry-run，不自动 publish。

这条路径既能持续补数据，又让任何下一位 AI 都能明确区分“允许的本机采样”与“尚未授权的自动抓取”。
