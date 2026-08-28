# 本机采集 CLI / GUI MVP

可移植 Python 工具。运行位置可以是本机或以后的远程机器；本轮只在本机用 fixture / dry-run 演练。

## 不做的事

- 不安装 Windows 计划任务、cron、服务
- 不向 `approval_status != approved` 的来源发 HTTP
- 不自动把 staging 发布到 `public_snapshot_entries`
- 来源配置没有 `score`，也不能覆盖网站展示用的 `site.score=50`

真实 HTTP、调度、公开发布必须由用户逐来源批准后另开任务。

## 默认值

| 字段 | 默认 |
|---|---|
| enabled | false |
| interval_minutes | 60 |
| max_items_per_run | 1000（`0` = 不限） |
| approval_status | draft |

手工运行忽略 `enabled=false`，但仍截断 `max_items_per_run`。未批准来源只读本地 fixture。

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

MySQL 连接只从仓库根目录 `.env` 的 `MYSQL_*` 读取，不要把密码写进本目录。`write-staging` 写入 `collection_staging_observations` 并打印匿名计数；失败时仍留下 `out/*.jsonl`。

## GUI

左侧来源列表，右侧可编辑字段、校验、手工 fixture dry-run 日志。形态参考 `D:\work\dock\PriceAI-Monitor\settings_gui.py`，但不包含自动下单、通知或计划任务。
