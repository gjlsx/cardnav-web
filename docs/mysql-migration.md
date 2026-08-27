# MySQL migration and deployment data flow

The public site uses MySQL only. PostgreSQL is not a runtime dependency.

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
