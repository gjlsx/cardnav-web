# ai.lovemoney.live 站点改造设计

## 目标

将 CardNav 公开站改造成 `ai.lovemoney.live`，以 MySQL `ailovemoney` 为唯一数据库，并发布至 `206.119.177.74` 的 HTTP 80 端口。LikeShop 现有的 `8086`、`8090`、`8095` 服务必须不受影响。

## 范围与品牌规则

- 网站、三语内容、SEO、robots、sitemap、结构化数据、环境变量示例和 README 统一使用 `ai.lovemoney.live`。
- 删除 CardNav/“卡网大全”及其旧域名、旧 Telegram、项目 GitHub、旧 X 账号等自有品牌信息。
- GitHub 按钮完全删除；Telegram、X 与 QQ 仅保留可替换的空链接图标占位。公告只显示纯文字，不能含跳转链接。
- 首页公共 Hero 区域（需求截图标记为 clear area 的整块区域）删除。
- 赞助商区域只显示图片；图片不得是链接，不显示商家名称、说明、套餐或价格。
- 第三方项目或来源的外部链接保留，除非它们属于旧 CardNav 自有入口；其文字不应暗示旧站点背书。

## 数据库设计

- 本地开发库：`127.0.0.1` 上的 MySQL `ailovemoney`；凭据只在本地环境变量中使用，绝不写入仓库。
- PostgreSQL 是弃用目标。核对结果：`cardnav` 仅有 4 张表且统计行数均为 0；迁移仍会先导出兼容数据（若存在）并在 MySQL 中创建运行时所需完整表结构。
- 运行时改用 `mysql2/promise`，参数统一为 `?`；PostgreSQL 专有 JSON、`DISTINCT ON`、`FILTER`、`ctid`、`$n` 参数和类型转换必须替换为等价 MySQL 查询。
- 数据库初始化脚本必须可重复执行；发布前从本机导出 SQL，服务器导入前先生成服务器侧备份。

## 部署设计

- 应用以 Astro standalone Node 服务运行，仅监听服务器回环地址的内部端口；Apache 的 `ai.lovemoney.live` 虚拟主机监听 `80` 并反向代理至该服务。
- 发布目录为独立的 `/www/wwwroot/ai.lovemoney.live`，不得复用 LikeShop 目录。
- 发布前先读取服务器当前 Apache 虚拟主机和监听端口。若 80 端口存在旧的非 LikeShop 站点，先备份配置后移除该站点；不触碰 `8086/8090/8095` 的配置或服务。
- VPS 密码只从 `D:\temp\aws\177.74 server.txt` 在当前进程读取。使用 Paramiko 进行非交互诊断、上传和验证；不记录或输出密码。

## 验收标准

- `npm test`、`npm run typecheck`、`npm run build` 均通过。
- 本机 MySQL 可初始化，应用不再依赖 PostgreSQL。
- 浏览器从首页检查：无旧域名/“卡网大全”、无 GitHub 按钮、无 Hero、公告为文字、Telegram/X/QQ 占位均不可跳转、赞助商仅有图片。
- 生产环境使用 `http://ai.lovemoney.live/` 验证 HTTP 200、页面渲染和浏览器控制台无新增错误；同时确认 LikeShop 三个既有端口继续响应。
