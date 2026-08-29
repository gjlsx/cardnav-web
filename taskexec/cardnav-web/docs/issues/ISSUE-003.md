# ISSUE-003 [P1]

Daily `ai.lovemoney.live` publish on `206.119.177.74` had no in-repo script. The previous helper lived only at `D:\temp\ailovemoney-p005\publish_p008.py` and imported local SQL.

## Changes

- Add `scripts/deploy/publish_ai_lovemoney.py` and `scripts/deploy/vps_session.py`
- Default publish is dist-only; keep remote `.env`; do not import local SQL
- Point the console publish action at the repo script
- Document command, parameters, and the 2026-08-30 run in `howtorunvpsnew.md`

## Verify

- `python -m unittest scripts.collection.tests.test_operations`
- Origin 80/443 and LikeShop 8086/8090/8095 stay HTTP 200 after publish
