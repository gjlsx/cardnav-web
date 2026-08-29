"""Read/write public website rows by stable key for the site-config tab."""
from __future__ import annotations

import json
from typing import Any

from .contracts import OverrideState, RecordKind, record_key
from .publisher import PublicPublisher, _site_id

HOMEPAGE_ANNOUNCEMENT_KEY = "homepage-announcement"


def normalize_homepage_announcement(payload: Any, fallback_message: str = "") -> str:
    message = payload.get("message") if isinstance(payload, dict) else ""
    return str(message or "").strip() or fallback_message


def load_homepage_announcement(repository, fallback_message: str = "") -> str:
    rows = repository.query("SELECT payload FROM public_snapshot_entries WHERE `key` = %s LIMIT 1", (HOMEPAGE_ANNOUNCEMENT_KEY,))
    if not rows:
        return fallback_message
    payload = rows[0].get("payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {}
    return normalize_homepage_announcement(payload, fallback_message)


def save_homepage_announcement(repository, message: str) -> str:
    normalized = " ".join(str(message or "").split())
    if not normalized:
        raise ValueError("公告内容不能为空")
    repository.upsert_snapshot(HOMEPAGE_ANNOUNCEMENT_KEY, {"message": normalized})
    repository.commit()
    return normalized


def list_public_rows(repository, kind: RecordKind) -> list[dict[str, Any]]:
    if kind is RecordKind.SHOP_PRODUCT:
        rows = repository.query("SELECT site_id, standard_product, name, price, price_number, currency_code, in_stock FROM shop_products ORDER BY id DESC LIMIT 300")
        return [{"record_key": f"shop_product:{(row.get('site_id') or '').replace('collected-','')}:{row.get('standard_product') or ''}", **row} for row in rows]
    if kind is RecordKind.GATEWAY_SITE:
        rows = repository.query("SELECT site_id, slug, name, host, score, region, benefit_text FROM gateway_sites ORDER BY score DESC, name ASC LIMIT 300")
        return [{"record_key": f"gateway_site:{row.get('host') or row.get('site_id')}", **row} for row in rows]
    if kind is RecordKind.OFFICIAL_PLAN:
        rows = repository.query("SELECT url_slug, country_code, display_name, price_text FROM official_prices ORDER BY display_order ASC LIMIT 300")
        return [{"record_key": f"official_plan:{row.get('url_slug')}:{row.get('country_code')}", **row} for row in rows]
    rows = repository.query("SELECT task_slug, model_name, rank, score FROM model_leaderboards ORDER BY task_slug, rank LIMIT 300")
    return [{"record_key": f"model_rank:{row.get('task_slug')}:{row.get('model_name')}", **row} for row in rows]


def save_manual_row(repository, kind: RecordKind, payload: dict[str, Any]) -> None:
    key = payload.get("record_key") or record_key(kind, host=str(payload.get("host") or payload.get("normalized_site") or ""), canonical_sku=str(payload.get("standard_product") or payload.get("model_or_plan") or ""), plan_slug=str(payload.get("url_slug") or ""), country_code=str(payload.get("country_code") or "US"), task_slug=str(payload.get("task_slug") or "coding"), model_name=str(payload.get("model_name") or ""))
    repository.set_manual_override(kind, key, OverrideState.MANUAL, payload)
    if kind is RecordKind.GATEWAY_SITE:
        repository.execute(
            "UPDATE gateway_sites SET region = %s, benefit_text = %s WHERE site_id = %s",
            (str(payload.get("region") or ""), str(payload.get("benefit_text") or ""), str(payload.get("site_id") or "")),
        )
        publisher = PublicPublisher()
        publisher.rebuild_snapshots(repository, {kind})
        repository.commit()
        return
    publisher = PublicPublisher()
    fake_row = {"id": 0, "record_key": key, "record_kind": kind.value, "source_id": payload.get("source_id") or "manual", "payload": payload}
    publisher._publish_row(repository, kind, fake_row)
    publisher.rebuild_snapshots(repository, {kind})
    repository.commit()


def hide_row(repository, kind: RecordKind, key: str) -> None:
    repository.set_manual_override(kind, key, OverrideState.HIDDEN)
    PublicPublisher().rebuild_snapshots(repository, {kind})
    repository.commit()
