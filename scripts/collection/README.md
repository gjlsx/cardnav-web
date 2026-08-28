# 本机采集 CLI / GUI MVP

可移植 Python 工具。运行位置可以是本机或以后的远程机器；本轮只在本机用 fixture / dry-run 演练。

## 安全边界与已批准方向

- 不安装 Windows 计划任务、cron、服务
- 不向 `approval_status != approved` 的来源发 HTTP
- 来源配置没有 `score`，也不能覆盖网站展示用的 `site.score=50`
- 不在 `ai.lovemoney.live` 生产站运行采集器
- MVP 不从本机直接连接远程 MySQL，也不提供 SSH 密码编辑器

已批准、字段白名单明确的来源会通过同一 raw → `collection_staging_observations` → 正式数据/快照流水线真实写入**本机** MySQL `ailovemoney`；未批准来源继续只读 fixture。完整公开响应只存入本机数据库的 raw 审计表并保留 30 天，绝不写入 Git、日志或导出文件。MVP 完成后，再单独规划本机直连远程 MySQL。

## 默认值

| 字段 | 默认 |
|---|---|
| enabled | false |
| interval_minutes | 60 |
| max_items_per_run | 1000（`0` = 不限） |
| approval_status | draft |

手工运行忽略 `enabled=false`，但仍截断 `max_items_per_run`。`enabled` 只控制 GUI 内的本地调度；未批准来源只读本地 fixture。手工覆盖/隐藏按稳定键阻止该条记录进入 staging/正式数据，批量来源响应仍会保存 raw 并处理其它记录。

合并：规范化站名去重；本站 API > 本站网页 > 聚合站（PriceAI > CardNav > OpenPrice）；同级最低价；高优先级覆盖有效字段，低优先级补空。

## 命令

```powershell
cd D:\work\dock\cardnav-web\scripts\collection
python collect.py check-config
python collect.py dry-run
python collect.py write-staging
python gui.py
python -m unittest tests.test_collection
```

MySQL 连接只从仓库根目录 `.env` 的 `MYSQL_*` 读取，不要把密码写进本目录。`collection_staging_observations` 是唯一 staging 表；旧 fixture 结果会以增量迁移兼容。当前命令仍是 MVP 入口，p013 后会统一写入 raw、staging 和正式数据并打印匿名计数。

## GUI

当前 GUI 是迁移前入口。总控台完成后由同一个 `python gui.py` 打开采集数据、网站配置、合作运维三根 Tab；采集数据含中转网站、卡网商品、官方网站、模型排行四个子 Tab，每页保存独立日志。形态参考 `D:\work\dock\PriceAI-Monitor\settings_gui.py`，但不包含自动下单或生产站采集。
