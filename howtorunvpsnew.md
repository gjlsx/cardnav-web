# AIGATE VPS 发布与验证

文档核对：2026-09-07；最近发布证据：2026-09-03，本轮未重新部署或探测线上。

当前目标：独立站 `aigate.live`，旧 `ai.lovemoney.live` 保留兼容跳转；与 LikeShop 同机但目录/服务/端口隔离。
本文是本项目日常发布入口，不是 LikeShop 文档副本。

## 0. 固定要求

1. 只发布 AIGATE；现有服务器目录和服务仍沿用 `ai.lovemoney.live` / `ai-lovemoney` 命名，不因品牌变更重命名。不要改 LikeShop 的 `8086` / `8090` / `8095` 虚拟主机或进程。
2. Apache `*:80` 和 `*:443` 承接 AIGATE 与旧域兼容，不应再把“仅旧域返回 200”当验收标准。LikeShop 继续走独立端口。
3. 应用是 Astro standalone Node，监听 `127.0.0.1:3101`，由 Apache 反代。
4. 应用数据库只使用服务器本地 MySQL/MariaDB `ailovemoney`。远程管理只使用专用低权限账号和受限白名单；不要把本机密码、dump 或 `.env` 写入本仓库。
5. 生产站只读展示。不要在 VPS 上运行 Python 采集器，不要安装采集计划任务。
6. 源站检查新旧域各自 Host/SNI，并检查公开新域浏览器；旧域预期 308 到 `https://aigate.live`，保持路径/查询参数。新域需实际内容响应。DNS/Cloudflare 与源站结果分开记录。
7. Windows 上不要用会残留的 `Start-Process ssh.exe` 反复探测；非交互诊断优先 Paramiko，凭据只从本机受控安全文件读取。
8. SSH 人工登录后如画面无输出，先按 Enter 再操作。

本机新采集使用 [Crawlee CLI](scripts/crawlee_collection/README.md)，采集与 merge/import 独立；`python scripts/collection/gui.py` 为 legacy 总控台，其合作运维 Tab 的发布按钮有二次确认。新版采集 GUI 当前未跟踪，不是新检出前置条件。不要把采集器装到生产机；本文仅说明操作方法，不自动授权执行。

## 0.1 文档分工

```text
howtorunvpsnew.md
  本项目日常入口：连接引用、构建、发布、验证、回滚、本地调试恢复。

docs/data-nav-and-collection.md
  产品与采集边界：已实现、可手工验证、必须用户批准的事项。

docs/mysql-migration.md
  MySQL 导出/导入和服务器目录事实。

D:\phpStudy\WWW\likeshop\howtorunvpsnew.md
  同机 LikeShop 发布入口。本项目发布时只核对其 8086/8090/8095 仍可用，不执行其发布脚本。
```

## 1. 连接信息

```text
站点: aigate.live（旧 ai.lovemoney.live 保留跳转）
发布目录: /www/wwwroot/ai.lovemoney.live
回滚目录: /www/wwwroot/ai.lovemoney.live-backups
systemd: ai-lovemoney.service
Node 监听: 127.0.0.1:3101
Node 二进制: /usr/bin/node
Apache 已有旧域 vhost: /etc/apache2/sites-available/ai.lovemoney.live.conf
Let’s Encrypt webroot: /var/www/letsencrypt
MySQL 库: ailovemoney（仅服务器本地）
```

连接材料从本机受控安全文件读取，与同机 LikeShop 指南使用的材料同一套；不粘贴其内容到 Git、tasklog 或聊天记录。变更前用 `apache2ctl -S` 核对实际新旧域 vhost，不根据旧文件名推定新域配置，也不批量覆盖站点配置。

首次使用私钥如遇 Windows OpenSSH 权限报错，只在本机对私钥文件收紧 ACL，不要把私钥复制进仓库。

自动诊断优先 Paramiko：`df`、`systemctl is-active apache2 ai-lovemoney`、`ss -lntp`、HTTP Host 头探测。需要 TUI 或长时间观察时再用人工 SSH。

## 1.1 远程 MySQL 管理边界

应用进程仍通过服务器本地回环 MySQL 运行；远程访问只用于受控开发和数据运维，不能把 `root` 暴露到公网。

- 白名单当前仅为 `216.144.231.55`（用户重复提供的同一 IP 按一个地址处理）。
- 使用专用账户，权限仅限 `ailovemoney.*` 的日常读写；不授予 `*.*`，不把 schema 管理权限交给远程采集器。
- 网络层用仅匹配 TCP/3306 的持久防火墙规则拒绝其它外部来源，同时必须保留服务器 `lo` 回环访问；不要为了此项启用、清空或重置整台服务器的 UFW。
- 本机忽略的 `.env` 可保存 `MYSQL_REMOTE_HOST`、`MYSQL_REMOTE_PORT`、`MYSQL_REMOTE_USER`、`MYSQL_REMOTE_PASSWORD`、`MYSQL_REMOTE_DATABASE`；这些值、导出的 SQL 和任何服务器密码都不得进 Git、任务日志或聊天。
- 变更白名单、撤销账户或排障前，先检查 `SHOW GRANTS`、`ss -lnt` 与 `systemctl status ai-lovemoney-mysql-firewall`。网页应用不可改用该远程账户。

## 2. 本地构建与样例数据

仓库：`D:\work\dock\cardnav-web`

```powershell
cd D:\work\dock\cardnav-web
pnpm install
pnpm test
pnpm run typecheck
pnpm run build
```

- `.env` 只在本机会话存在；`MYSQL_PASSWORD` 等不要提交。
- `seed:reference-samples` 会写实体和公开快照，仅可在明确批准的隔离样例数据库执行；不是日常启动、构建或发布前置步骤。已有真实数据时不要运行。
- 构建产物在 `dist/`。本地 `pnpm run dev` 仍用 `PORT=3101`，不要把生产 `dist` 当成 dev 页面来源。

日常发布会把本机 `ailovemoney` 导出为临时 SQL，上传后在服务器上用本地 MySQL 直接导入，导入后删除临时文件。不要把 SQL dump 加入 git，也不要把本机连接串写进远程脚本。手动导出（脚本已内嵌，一般不必单独跑）：

```powershell
.\scripts\export-mysql.ps1 -OutputPath D:\temp\ailovemoney.sql
```

## 3. 当前服务器布局

```text
Apache: apache2，*:80 与 *:443 承接 AIGATE 新域及旧域跳转
Node: systemd ai-lovemoney.service -> 127.0.0.1:3101
数据库: 服务器本地 MariaDB/MySQL，库名 ailovemoney
LikeShop 隔离: dtch.yg2022.top 的 8086/8090/8095 保持原状
```

不要把 systemd `ExecStart` 指到 `/usr/local/bin/node` 若该路径是 `/root/.hermes` 的符号链接：`www-data` 不能遍历 `/root`。使用 `/usr/bin/node`。

Apache 反代只转到回环 3101，不要把 Node 绑到公网。

## 4. 正式发布与恢复本地调试

标准发布脚本（仓库内，可复用；凭据仍只从本机受控文件读取）：

```powershell
cd D:\work\dock\cardnav-web
pnpm test
pnpm run typecheck
pnpm run build
python scripts/deploy/publish_ai_lovemoney.py
```

脚本行为（日常发布 = `dist` + 本机 SQL 导入服务器）：

| 项 | 值 |
|---|---|
| 目标 | `206.119.177.74`，用户 `root` |
| 凭据 | `D:\temp\aws\177.74 server.txt`；远程 MySQL 密码从 LikeShop 本机 deploy config 读取；本机 dump 用仓库 `.env` 的 `MYSQL_*` |
| 上传 | `dist/` tar + 本机 `ailovemoney` SQL；不上传 `.env` |
| 备份 | 站点 `ai.lovemoney.live-<timestamp>.tar.gz`；导入前再 `mysqldump` 远程库为 `ailovemoney-<timestamp>.sql` |
| 数据库 | `scripts/export-mysql.ps1` 导出本机库，服务器 `mysql < dump` 直接导入 |
| 重启 | 只 `systemctl restart ai-lovemoney` |
| 验证 | origin 80/443 Host 头、LikeShop 8086/8090/8095、无采集进程/timer、`public_snapshot_entries` / `gateway_sites` 计数 |
| 禁止 | 改 LikeShop vhost、覆盖远程 `.env`、在生产跑采集器、把 dump 提交进 git |

控制台「发布」二次确认短语 `CONFIRM PUBLISH AI.LOVEMONEY.LIVE` 也调用同一脚本。

脚本内 HTTP 探测主要覆盖旧域且不会替代新域浏览器验收；必须追加第 5–6 节检查，不能把脚本退出成功当作完整发布通过。确认短语和旧目录名称保留现状，不在文档任务中修改运行协议。

2026-08-30 05:09 按本表发布：本机 `export-mysql.ps1 --result-file` 导出后服务器直接导入。导入后 `gateway_sites=422`、`gateway_model_prices=2283`、`public_snapshot_entries=9`。远程库备份 `ailovemoney-20260830-050931.sql`。origin 80/443 与 LikeShop 三端口均为 200。此前 PowerShell `Out-File` 会把 dump 转坏，导出已改为 mysqldump `--result-file`。

上述为历史记录。较新的 2026-09-03 记录为 426 个 gateway_sites、2344 条 gateway_model_prices、11 个 snapshots；旧域 308，新域浏览器可用，LikeShop 三端口 200。详见 [发布 QA](taskexec/cardnav-web/docs/qa/p0_codex_t09030447.p003.md)。这些数值不是下一次发布的固定目标；每次记录实际结果，不足时查原因而不是灌样例补数。

推荐手工顺序与脚本一致：本机验证通过后再覆盖远程 `dist` 并导入本机 SQL，然后重启 `ai-lovemoney`，最后恢复本机 `pnpm run dev`。

1. 本机完成第 2 节命令，浏览器检查 `http://127.0.0.1:3101` 的 `/`、`/shops`、`/llm-gateway`、`/official-price`、`/model-leaderboard`、`/guide`。
2. 运行 `python scripts/deploy/publish_ai_lovemoney.py`（备份站点与远程库、同步 `dist`、导入本机 SQL、重启与端口验证）。不要上传本机 `.env`。
3. 不要重载或改写 LikeShop vhost。
4. 发布结束后回到本机：

```powershell
cd D:\work\dock\cardnav-web
$env:PORT='3101'
pnpm run dev
```

本地浏览器入口仍是 `http://127.0.0.1:3101/`。不要把 `ai.lovemoney.live` 指到本机。

远程 `.env` 保留服务器自己的配置，禁止用本机文件整份覆盖。源码 canonical 默认是 `https://aigate.live`；若服务器设置 `PUBLIC_SITE_URL`，应在获批发布时核对其是否与新主域一致，而不是照抄旧域示例。本轮未读取或修改远程环境变量。

## 5. 验证命令

在已认证会话中执行，输出里的秘密自行忽略，不要回写本文。

```bash
systemctl is-active apache2 ai-lovemoney
apache2ctl -S
ss -lntp | grep -E ':80|:443|:3101|:8086|:8090|:8095'
curl -sI -H 'Host: ai.lovemoney.live' http://127.0.0.1/
curl -skI -H 'Host: ai.lovemoney.live' https://127.0.0.1/
curl -sI -H 'Host: aigate.live' http://127.0.0.1/
curl -sI --resolve aigate.live:443:127.0.0.1 https://aigate.live/
curl -sI http://127.0.0.1:8086/shop/
curl -sI http://127.0.0.1:8090/mobile/
curl -sI http://127.0.0.1:8095/admin/
```

本机额外检查：

```powershell
curl.exe -sI https://ai.lovemoney.live/
curl.exe -sI https://aigate.live/
curl.exe -sI http://dtch.yg2022.top:8086/shop/
curl.exe -sI http://dtch.yg2022.top:8090/mobile/
curl.exe -sI http://dtch.yg2022.top:8095/admin/
```

LikeShop 三个地址必须仍返回可用 HTTP 响应。旧域 80/443 应返回到新域的 308；新域 HTTPS 应返回本站内容，而不是 LikeShop。使用 `-k` 的旧域探测只证明路由，不能证明证书有效；公开 HTTPS 仍需无忽略证书的检查和浏览器结果。

确认服务器没有采集进程或采集 schedule：

```bash
systemctl list-timers --all
ps aux | grep -E 'collection|collect.py' | grep -v grep
```

发现采集器或计划任务则本次验收不通过：先确认是否属于本项目，按获批范围处理；不得误停同机其他服务。

## 6. 浏览器入口

发布后至少打开：

```text
https://aigate.live/
https://aigate.live/shops
https://aigate.live/llm-gateway
https://aigate.live/official-price
https://aigate.live/model-leaderboard
https://aigate.live/guide
```

从首页进入模型排行或官方网站，再点一条内部关联到卡网/中转网站。desktop 与 390px、zh/en/ru 至少各看一次主导航。

另从 `https://ai.lovemoney.live/llm-gateway?model=gpt` 进入，核对最终新域、路径和查询参数；直接打开新域不能替代兼容跳转验收。

隔离检查：

```text
http://dtch.yg2022.top:8086/shop/
http://dtch.yg2022.top:8090/mobile/
http://dtch.yg2022.top:8095/admin/
```

## 7. 端口

| 端口 | 用途 | 发布时 |
|---|---|---|
| 80 / 443 | AIGATE 新域及旧域兼容 Apache | 新域本站、旧域 308 |
| 3101 | Node 回环 | 只绑 127.0.0.1 |
| 8086 | LikeShop shop | 不得改动 |
| 8090 | LikeShop mobile | 不得改动 |
| 8095 | LikeShop admin | 不得改动 |

## 8. 回滚与注意事项

- 回滚站点：把 `/www/wwwroot/ai.lovemoney.live-backups/ai.lovemoney.live-<timestamp>.tar.gz` 解回发布目录，重启 `ai-lovemoney`。
- 回滚数据库：`python scripts/deploy/restore_remote_mysql.py <timestamp>`，对应文件 `ailovemoney-<timestamp>.sql`。回滚会替换数据，须确认目标与授权；不要 `a2dissite` LikeShop 配置。停本站前以 `apache2ctl -S` 确认实际承接新旧域的配置，不盲目只禁用一个旧名文件。
- 不要 `pkill node` 或无筛选 `pkill ssh`；只操作 `ai-lovemoney.service`。
- 不要在生产安装 Windows 计划任务、cron collector 或 Python GUI。
- 记录实际发布命令时脱敏：去掉密码、密钥路径中的秘密、dump 全文、cookie。
- 数据流细节见 `docs/mysql-migration.md`。产品边界见 `docs/data-nav-and-collection.md`。
