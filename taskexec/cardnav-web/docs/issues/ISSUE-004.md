# ISSUE-004 [P1]

Daily VPS publish must export local `ailovemoney` SQL and import it on 206.119.177.74. Dist-only is not the standard.

## Changes

- `scripts/deploy/publish_ai_lovemoney.py` dumps local MySQL via `scripts/export-mysql.ps1`, uploads the dump, backs up the remote database, then `mysql < dump`
- Temporary SQL is not committed; remote tmp files are deleted after import
- `howtorunvpsnew.md` records this as the reusable publish path

## Verify

- 2026-08-30 import: `gateway_sites=422`, `gateway_model_prices=2283`, `public_snapshot_entries=9`
- Origin 80/443 and LikeShop 8086/8090/8095 HTTP 200
- Dump body is not committed
