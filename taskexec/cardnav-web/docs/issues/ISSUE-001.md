# ISSUE-001 [P1]

Port 80 on 206.119.177.74 must serve only `ai.lovemoney.live`. The previous LikeShop `dtch.yg2022.top` vhost on `*:80` is not needed.

## Changes

- Backed up `/etc/apache2/sites-available/dtch.yg2022.top.conf`
- Removed the `*:80` VirtualHost from that file
- Left LikeShop `*:8086`, `*:8090`, `*:8095` unchanged
- Apache `*:80` and `*:443` now name only `ai.lovemoney.live`

## Verify

- `apache2ctl -S`: `*:80` and `*:443` → `ai.lovemoney.live`
- `Host: ai.lovemoney.live` and raw IP `:80` return AI LoveMoney
- `https://ai.lovemoney.live/` browser title is AI LoveMoney
- `dtch.yg2022.top:8086/shop/`, `:8090/mobile/`, `:8095/admin/` still HTTP 200
