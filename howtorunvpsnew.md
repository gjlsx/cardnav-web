# AI LoveMoney VPS 发布与验证

更新时间：2026-08-29  
当前目标：独立站 `ai.lovemoney.live`，与 LikeShop `dtch.yg2022.top` 同机但目录/服务/端口隔离。  
本文是本项目日常发布入口，不是 LikeShop 文档副本。

## 0. 固定要求

1. 只发布 `ai.lovemoney.live`。不要改 LikeShop 的 `8086` / `8090` / `8095` 虚拟主机或进程。
2. Apache `*:80` 和 `*:443` 只服务 `ai.lovemoney.live`。LikeShop 继续走独立端口。
3. 应用是 Astro standalone Node，监听 `127.0.0.1:3101`，由 Apache 反代。
4. 应用数据库只使用服务器本地 MySQL/MariaDB `ailovemoney`。远程管理只使用专用低权限账号和受限白名单；不要把本机密码、dump 或 `.env` 写入本仓库。
5. 生产站只读展示。不要在 VPS 上运行 Python 采集器，不要安装采集计划任务。
6. DNS 走 Cloudflare 时，源站验证使用 origin IP + `Host: ai.lovemoney.live`，或已解析的 `https://ai.lovemoney.live/`。
7. Windows 上不要用会残留的 `Start-Process ssh.exe` 反复探测；非交互诊断优先 Paramiko，凭据只从本机受控安全文件读取。
8. SSH 人工登录后如画面无输出，先按 Enter 再操作。

本机日常数据采集与正式数据编辑使用 `python scripts/collection/gui.py`，不要把采集器装到生产机。合作运维 Tab 的发布按钮二次确认后才按本文执行。

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
站点: ai.lovemoney.live
发布目录: /www/wwwroot/ai.lovemoney.live
回滚目录: /www/wwwroot/ai.lovemoney.live-backups
systemd: ai-lovemoney.service
Node 监听: 127.0.0.1:3101
Node 二进制: /usr/bin/node
Apache vhost: /etc/apache2/sites-available/ai.lovemoney.live.conf
Let’s Encrypt webroot: /var/www/letsencrypt
MySQL 库: ailovemoney（仅服务器本地）
```

用户名、密码、私钥、跳板和 dump 路径不写在本文件。从本机受控安全文件读取，与同机 LikeShop 指南使用的连接材料同一套。不要把该文件内容粘贴进 git、tasklog 或聊天记录。

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
pnpm run seed:reference-samples
pnpm test
pnpm run typecheck
pnpm run build
```

- `.env` 只在本机会话存在；`MYSQL_PASSWORD` 等不要提交。
- `seed:reference-samples` 写入本机 `ailovemoney` 和公开快照，供页面验证。它不是生产采集。
- 构建产物在 `dist/`。本地 `pnpm run dev` 仍用 `PORT=3101`，不要把生产 `dist` 当成 dev 页面来源。

如需把本机样例同步到服务器，只导出最小 SQL 到本机临时目录，经已认证通道上传，导入后删除临时文件。不要把 SQL dump 加入 git。

```powershell
$env:MYSQL_PASSWORD = '<local password>'   # 仅当前会话
.\scripts\export-mysql.ps1 -OutputPath D:\temp\ailovemoney.sql
```

服务器导入时使用服务器本地 MySQL 环境，不要把本机连接串写进远程脚本。

## 3. 当前服务器布局

```text
Apache: apache2，*:80 与 *:443 仅 ai.lovemoney.live
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

脚本行为（默认只发 `dist`，这是日常发布）：

| 项 | 值 |
|---|---|
| 目标 | `206.119.177.74`，用户 `root` |
| 凭据 | `D:\temp\aws\177.74 server.txt`；远程 MySQL 密码从 LikeShop 本机 deploy config 读取 |
| 上传 | 仅 `dist/` tar，不上传 `.env`、不导入本机 SQL |
| 备份 | `/www/wwwroot/ai.lovemoney.live-backups/ai.lovemoney.live-<timestamp>.tar.gz` |
| 缺列 | 幂等补 `gateway_sites.region`、`benefit_text` |
| 重启 | 只 `systemctl restart ai-lovemoney` |
| 验证 | origin 80/443 Host 头、LikeShop 8086/8090/8095、无采集进程/timer |
| 禁止 | 改 LikeShop vhost、覆盖远程 `.env`、在生产跑采集器 |

控制台「发布」二次确认短语 `CONFIRM PUBLISH AI.LOVEMONEY.LIVE` 也调用同一脚本。旧的 `D:\temp\ailovemoney-p005\publish_p008.py` 会整库导入本机 SQL，**不要当日常发布**。

2026-08-30 04:50 Asia/Hong_Kong 按上表发布：备份 `ai.lovemoney.live-20260830-050029.tar.gz`；origin HTTP/HTTPS 200；`/llm-gateway` 可见「最近刷新」与「即将上线」；LikeShop 三端口 200；无采集器。本机 `https://ai.lovemoney.live/` 与 `dtch.yg2022.top:8086/8090/8095` 均为 HTTP 200。

推荐手工顺序与脚本一致：本机验证通过后再覆盖远程 `dist`，然后重启 `ai-lovemoney`，最后恢复本机 `pnpm run dev`。

1. 本机完成第 2 节命令，浏览器检查 `http://127.0.0.1:3101` 的 `/`、`/shops`、`/llm-gateway`、`/official-price`、`/model-leaderboard`、`/guide`。
2. 运行 `python scripts/deploy/publish_ai_lovemoney.py`（内含远程备份、同步 `dist`、缺列迁移、重启与端口验证）。不要上传本机 `.env`。
3. 如需更新样例快照，另做脱敏 SQL 导入，核对 `public_snapshot_entries` 计数后再切流量；这不是默认发布步骤。
4. 不要重载或改写 LikeShop vhost。
5. 发布结束后回到本机：

```powershell
cd D:\work\dock\cardnav-web
$env:PORT='3101'
pnpm run dev
```

本地浏览器入口仍是 `http://127.0.0.1:3101/`。不要把 `ai.lovemoney.live` 指到本机。

远程 `.env` 只保留服务器自己的 `MYSQL_*`、`PORT=3101`、`PUBLIC_SITE_URL=https://ai.lovemoney.live`。禁止用本机 `.env` 整文件覆盖。

## 5. 验证命令

在已认证会话中执行，输出里的秘密自行忽略，不要回写本文。

```bash
systemctl is-active apache2 ai-lovemoney
ss -lntp | grep -E ':80|:443|:3101|:8086|:8090|:8095'
curl -sI -H 'Host: ai.lovemoney.live' http://127.0.0.1/
curl -skI -H 'Host: ai.lovemoney.live' https://127.0.0.1/
curl -sI http://127.0.0.1:8086/shop/
curl -sI http://127.0.0.1:8090/mobile/
curl -sI http://127.0.0.1:8095/admin/
```

本机额外检查：

```powershell
curl.exe -sI https://ai.lovemoney.live/
curl.exe -sI http://dtch.yg2022.top:8086/shop/
curl.exe -sI http://dtch.yg2022.top:8090/mobile/
curl.exe -sI http://dtch.yg2022.top:8095/admin/
```

LikeShop 三个地址必须仍返回可用 HTTP 响应。`ai.lovemoney.live` 的 80/443 必须是本站，而不是 LikeShop。

确认服务器没有采集进程或采集 schedule：

```bash
systemctl list-timers --all
ps aux | grep -E 'collection|collect.py' | grep -v grep
```

有采集器或计划任务则视为发布失败，先停掉再查。

## 6. 浏览器入口

发布后至少打开：

```text
https://ai.lovemoney.live/
https://ai.lovemoney.live/shops
https://ai.lovemoney.live/llm-gateway
https://ai.lovemoney.live/official-price
https://ai.lovemoney.live/model-leaderboard
https://ai.lovemoney.live/guide
```

从首页进入模型排行或官方网站，再点一条内部关联到卡网/中转网站。desktop 与 390px、zh/en/ru 至少各看一次主导航。

隔离检查：

```text
http://dtch.yg2022.top:8086/shop/
http://dtch.yg2022.top:8090/mobile/
http://dtch.yg2022.top:8095/admin/
```

## 7. 端口

| 端口 | 用途 | 发布时 |
|---|---|---|
| 80 / 443 | 仅 `ai.lovemoney.live` Apache | 必须保持本站 |
| 3101 | Node 回环 | 只绑 127.0.0.1 |
| 8086 | LikeShop shop | 不得改动 |
| 8090 | LikeShop mobile | 不得改动 |
| 8095 | LikeShop admin | 不得改动 |

## 8. 回滚与注意事项

- 回滚：把 `/www/wwwroot/ai.lovemoney.live-backups/<timestamp>` 拷回发布目录，重启 `ai-lovemoney`。不要 `a2dissite` LikeShop 配置。停本站时只禁用 `ai.lovemoney.live.conf`。
- 不要 `pkill node` 或无筛选 `pkill ssh`；只操作 `ai-lovemoney.service`。
- 不要在生产安装 Windows 计划任务、cron collector 或 Python GUI。
- 记录实际发布命令时脱敏：去掉密码、密钥路径中的秘密、dump 全文、cookie。
- 数据流细节见 `docs/mysql-migration.md`。产品边界见 `docs/data-nav-and-collection.md`。
