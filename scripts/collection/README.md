# Legacy 本机采集 CLI / GUI MVP

> 此目录保留供历史回溯，暂不删除；新的正式采集入口是 `scripts/crawlee_collection/` 的 Crawlee + Playwright 程序。新 CLI 和新 worker 不调用本目录的旧采集入口。

本机网站总控台（Python/Tkinter）。入口：`python gui.py`。根 Tab：采集数据、网站配置、合作运维。采集子 Tab：中转网站、卡网商品、官方网站、模型排行。每页底部独立日志。

## 安全边界与已批准方向

- 不安装 Windows 计划任务、cron、服务
- 不向 `approval_status != approved` 的来源发 HTTP
- 来源配置没有 `score`，也不能覆盖网站展示用的 `site.score=50`
- 不在 `ai.lovemoney.live` 生产站运行采集器
- MVP 不从本机直接连接远程 MySQL，也不提供 SSH 密码编辑器

已批准、字段白名单明确的来源会将来源 raw payload 和简单清洗后的统一 `collection_raw_records` 真实写入**本机** MySQL `ailovemoney`；未批准来源继续只读 fixture。只有独立的人工或已显式启用定时 `merge-import` 才能从 raw 合并去重并写入运行时数据/快照，入库即发布。完整公开响应只存入本机数据库的 raw 审计表并保留 30 天，绝不写入 Git、日志或导出文件。MVP 完成后，再单独批准本机直连运行时服务器 MySQL。

## 默认值

| 字段 | 默认 |
|---|---|
| enabled | false |
| interval_minutes | 60 |
| max_items_per_run | 1000（`0` = 不限） |
| approval_status | draft |

手工运行忽略 `enabled=false`，但仍截断 `max_items_per_run`。`enabled` 只控制 GUI 内的本地采集调度；未批准来源只读本地 fixture。手工覆盖/隐藏不阻止 raw 保存，但按稳定键阻止后续 merge-import 更新运行时数据。

合并：规范化站名去重；本站 API > 本站网页 > 聚合站（PriceAI > CardNav > OpenPrice）；同级最低价；高优先级覆盖有效字段，低优先级补空。

## 命令

```powershell
cd D:\work\dock\cardnav-web\scripts\collection
python collect.py check-config
python collect.py dry-run
python collect.py collect-raw
python collect.py merge-import --batch <batch-id>
python gui.py
python -m unittest discover -s tests
```

合作运维备份/恢复/发布先预检，再输入确认短语后才会执行。发布遵循仓库根目录 `howtorunvpsnew.md`，禁止 SSH 密码编辑和改动 LikeShop `8086/8090/8095`。进程内调度默认关闭，关闭 GUI 即停止。

MySQL 连接只从仓库根目录 `.env` 的 `MYSQL_*` 读取。`collection_raw_records` 是项目固定、来源无关的 raw 格式；`collection_staging_observations` 是唯一旧 staging 兼容表。`collect-raw` 对 draft 用 fixture、对 approved+allowlist 发真实 HTTP，但都只入 raw；`merge-import` 才合并并事务写本机运行时表/快照。

## GUI

总控台由同一个 `python gui.py` 打开采集数据、网站配置、合作运维三根 Tab；采集数据含中转网站、卡网商品、官方网站、模型排行四个子 Tab，每页保存独立日志。来源列表是动态的：选中一项后可“抓取一次”“开始循环抓取”“停止选中来源”或“测试选中来源”。循环仅影响该来源，按它自己的 `interval_minutes` 运行且不会重叠；停止会设置运行标志，当前 HTTP 完成后不会继续清洗/raw 入库。merge-import 是独立动作。

测试按钮只执行项目内固定的 `scripts/collection/source_tests/test.py --source <id>`，其 stdout/stderr 和退出状态会写入该页日志；它是本地 fixture 诊断，不执行任意 shell 命令，也不发送 HTTP。形态参考 `D:\work\dock\PriceAI-Monitor\settings_gui.py`，但不包含自动下单或生产站采集。
