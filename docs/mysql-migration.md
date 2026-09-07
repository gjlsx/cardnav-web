# MySQL migration and deployment data flow

The public site uses MySQL only. PostgreSQL is not a runtime dependency.

Documentation checked on 2026-09-07. Migration history below is not a live database inventory. Current product/operating state is in [CURRENT_STATUS](CURRENT_STATUS.md); routine deployment follows [the deployment guide](../howtorunvpsnew.md). Do not run exports/imports or sample seed merely to validate documentation.

## Local development database

Configure the following locally (do not commit the password):

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=ailovemoney
```

Initialize the schema by running the MySQL schema test or the deployment initializer. The current migration copied the non-empty PostgreSQL public snapshots to `ailovemoney`; it found no historical `shop_sites`, `shop_products`, or `shop_search_terms` records.

## Export from local MySQL

Set `MYSQL_PASSWORD` only in the shell session, then run:

```powershell
$env:MYSQL_PASSWORD = '<local password>' # the script maps this only to the client process
.\scripts\export-mysql.ps1 -OutputPath D:\temp\ailovemoney.sql
```

The generated SQL is data and may contain public site content. Do not add it to Git.

## Import on the VPS

Copy the SQL file over the authenticated deployment channel. On the server, use its local MySQL credentials in the process environment and import it with the server MySQL client:

```bash
mysql --host=127.0.0.1 --port=3306 --user=root < /path/to/ailovemoney.sql
```

The deployment task must verify `public_snapshot_entries` counts before switching Apache traffic to the new site.

## Current production layout

- App directory: `/www/wwwroot/ai.lovemoney.live`
- systemd unit: `ai-lovemoney.service` (Node listens on `127.0.0.1:3101`)
- Apache vhost: `/etc/apache2/sites-available/ai.lovemoney.live.conf` (`*:80` and `*:443` only; port 80 is not used by LikeShop)
- Let's Encrypt webroot: `/var/www/letsencrypt`
- Rollback copies: `/www/wwwroot/ai.lovemoney.live-backups`
- Do not edit LikeShop vhosts for `8086/8090/8095`

Public branding/canonical domain is now `aigate.live`; `ai.lovemoney.live` is the legacy redirect domain. The directory, backup and systemd names above remain unchanged. The vhost filename is an existing legacy reference, not proof that it alone handles both domains: inspect `apache2ctl -S` before an authorized deployment. The September 3 QA recorded legacy-domain 308 and a successful browser arrival on AIGATE, not legacy-domain 200 as the desired state.

Local raw collection, local merge/import and VPS SQL import are separate operations. The collector writes only local raw data; explicit merge/import updates the configured local runtime tables/snapshots. The normal deploy script backs up the remote database before importing the local runtime state. A successful local merge is not evidence that the remote site was updated. Preserve the remote environment file and verify both new/legacy domains after import.

The Node binary used by systemd is `/usr/bin/node`. Do not point the unit at `/usr/local/bin/node` if that path is a symlink into `/root/.hermes`, because `www-data` cannot traverse `/root`.
