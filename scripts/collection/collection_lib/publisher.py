"""Publish approved staging rows into public tables and snapshots in one transaction."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .contracts import RecordKind


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _site_id(host: str) -> str:
    return f"collected-{host.replace(':', '-').replace('/', '-')[:50]}"


class PublicPublisher:
    def publish_run(self, repository, run_id: str) -> dict[str, int]:
        stats = {"published": 0, "skipped_manual": 0}
        kinds: set[RecordKind] = set()
        for row in repository.fetch_pending_staging(run_id):
            kind = RecordKind(row["record_kind"])
            key = str(row["record_key"])
            if repository.has_manual_override(kind, key):
                repository.mark_staging(row["id"], "skipped")
                stats["skipped_manual"] += 1
                continue
            self._publish_row(repository, kind, row)
            repository.mark_staging(row["id"], "published")
            stats["published"] += 1
            kinds.add(kind)
        if kinds:
            self.rebuild_snapshots(repository, kinds)
        return stats

    def _publish_row(self, repository, kind: RecordKind, row: dict[str, Any]) -> None:
        payload = row.get("payload") or {}
        if kind is RecordKind.SHOP_PRODUCT:
            self._publish_shop(repository, row, payload)
        elif kind is RecordKind.GATEWAY_SITE:
            self._publish_gateway(repository, row, payload)
        elif kind is RecordKind.OFFICIAL_PLAN:
            self._publish_official(repository, row, payload)
        elif kind is RecordKind.MODEL_RANK:
            self._publish_rank(repository, row, payload)

    def _publish_shop(self, repository, row: dict[str, Any], payload: dict[str, Any]) -> None:
        host = str(payload.get("normalized_site") or "")
        site_id = _site_id(host)
        sku = str(payload.get("model_or_plan") or "")
        price = payload.get("price")
        sampled = str(payload.get("observed_at") or _now())
        repository.execute(
            "INSERT INTO shop_sites (id, name, url, last_product_refresh_success_at, score, sponsor, product_count, in_stock_product_count, status, type, family) "
            "VALUES (%s, %s, NULL, %s, 50, FALSE, 1, 1, 'online', 'cardShop', 'collected') "
            "ON DUPLICATE KEY UPDATE name = VALUES(name), last_product_refresh_success_at = VALUES(last_product_refresh_success_at), score = 50",
            (site_id, payload.get("site_name") or host, sampled[:19].replace("T", " ")),
        )
        repository.execute(
            "DELETE FROM shop_products WHERE site_id = %s AND standard_product = %s AND source_id = %s",
            (site_id, sku, str(payload.get("source_id") or row.get("source_id") or "")),
        )
        repository.execute(
            "INSERT INTO shop_products (site_id, source_id, standard_product, platform, product_type, category_name, name, price, price_number, price_unit, currency_code, in_stock, sampled_at, is_sample, refreshed_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, FALSE, %s)",
            (
                site_id, str(payload.get("source_id") or row.get("source_id") or ""), sku,
                payload.get("platform_family") or "", payload.get("billing_unit") or "", payload.get("platform_family") or "",
                sku, str(price), price, payload.get("currency") or "CNY", payload.get("currency") or "CNY",
                sampled[:19].replace("T", " "), sampled[:19].replace("T", " "),
            ),
        )

    def _publish_gateway(self, repository, row: dict[str, Any], payload: dict[str, Any]) -> None:
        host = str(payload.get("normalized_site") or "")
        site_id = _site_id(host)
        slug = host.replace(".", "-")[:80]
        sampled = str(payload.get("observed_at") or _now())[:19].replace("T", " ")
        repository.execute(
            "INSERT INTO gateway_sites (site_id, url, status, name, family, type, slug, host, score, source_id, sampled_at, is_sample, created_at, summary) "
            "VALUES (%s, NULL, 'online', %s, %s, 'gateway', %s, %s, 50, %s, %s, FALSE, %s, %s) "
            "ON DUPLICATE KEY UPDATE name = VALUES(name), family = VALUES(family), score = 50, sampled_at = VALUES(sampled_at)",
            (site_id, payload.get("site_name") or host, payload.get("platform_family") or "collected", slug, host,
             str(payload.get("source_id") or row.get("source_id") or ""), sampled, sampled, payload.get("summary") or ""),
        )
        model_id = str(payload.get("model_or_plan") or "")
        if model_id:
            repository.execute(
                "INSERT INTO gateway_model_coverage (site_id, model_id, model_family, source_id, observed_at, is_sample) "
                "VALUES (%s, %s, %s, %s, %s, FALSE) ON DUPLICATE KEY UPDATE model_family = VALUES(model_family), observed_at = VALUES(observed_at)",
                (site_id, model_id, payload.get("model_family") or payload.get("platform_family") or "Other",
                 str(payload.get("source_id") or row.get("source_id") or ""), sampled),
            )

    def _publish_official(self, repository, row: dict[str, Any], payload: dict[str, Any]) -> None:
        plan = str(payload.get("plan_slug") or payload.get("model_or_plan") or "")
        country = str(payload.get("country_code") or payload.get("region") or "US")[:2].upper()
        sampled = str(payload.get("observed_at") or _now())[:19].replace("T", " ")
        price = payload.get("price") or 0
        repository.execute(
            "DELETE FROM official_prices WHERE url_slug = %s AND country_code = %s AND source_id = %s",
            (plan, country, str(payload.get("source_id") or row.get("source_id") or "")),
        )
        repository.execute(
            "INSERT INTO official_prices (app_slug, plan_slug, app_name, plan_name, display_name, url_slug, is_default, display_order, country_code, country_label, currency_code, price_text, price_value, cny_price, usd_price, rub_price, source_id, sampled_at, is_sample, fetched_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, FALSE, 100, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s)",
            (plan.split("-")[0], plan, plan, plan, plan, plan, country, country, payload.get("currency") or "USD",
             str(price), price, price, price, price, str(payload.get("source_id") or row.get("source_id") or ""), sampled, sampled),
        )

    def _publish_rank(self, repository, row: dict[str, Any], payload: dict[str, Any]) -> None:
        task = str(payload.get("task_slug") or payload.get("platform_family") or "coding")
        model = str(payload.get("model_name") or payload.get("model_or_plan") or "")
        sampled = str(payload.get("observed_at") or _now())[:19].replace("T", " ")
        score = payload.get("price") or payload.get("confidence") or 0
        repository.execute(
            "DELETE FROM model_leaderboards WHERE task_slug = %s AND model_name = %s AND source_id = %s",
            (task, model, str(payload.get("source_id") or row.get("source_id") or "")),
        )
        repository.execute(
            "INSERT INTO model_leaderboards (task_slug, source_name, source_url, source_group_slug, source_board_slug, rank, model_name, model_family, score, source_id, sampled_at, is_sample, fetched_at) "
            "VALUES (%s, %s, '', %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s)",
            (task, payload.get("source_id") or "collected", task, task, int(payload.get("rank") or 1), model,
             payload.get("model_family") or payload.get("platform_family") or "", score,
             str(payload.get("source_id") or row.get("source_id") or ""), sampled, sampled),
        )

    def rebuild_snapshots(self, repository, kinds: set[RecordKind]) -> None:
        if RecordKind.SHOP_PRODUCT in kinds:
            self._rebuild_shop_snapshot(repository)
        if RecordKind.GATEWAY_SITE in kinds:
            self._rebuild_gateway_snapshot(repository)
        if RecordKind.OFFICIAL_PLAN in kinds:
            self._rebuild_official_snapshot(repository)
        if RecordKind.MODEL_RANK in kinds:
            self._rebuild_rank_snapshot(repository)

    def _rebuild_shop_snapshot(self, repository) -> None:
        products = repository.query(
            "SELECT shop_products.site_id, shop_sites.name AS site_name, shop_sites.score AS site_score, shop_products.standard_product, shop_products.platform, shop_products.product_type, shop_products.category_name, shop_products.name, shop_products.price, shop_products.price_number, shop_products.price_unit, shop_products.currency_code, shop_products.in_stock, shop_products.sampled_at, shop_products.is_sample, shop_products.source_id "
            "FROM shop_products LEFT JOIN shop_sites ON shop_sites.id = shop_products.site_id"
        )
        sites = repository.query("SELECT id, name, url, last_product_refresh_success_at, score, sponsor FROM shop_sites")
        payload = {
            "sites": [
                {
                    "id": site["id"], "name": site["name"], "url": site.get("url") or "",
                    "lastProductRefreshSuccessAt": str(site.get("last_product_refresh_success_at") or ""),
                    "lastProductRefreshSuccessTime": str(site.get("last_product_refresh_success_at") or ""),
                    "score": float(site.get("score") or 50), "sponsor": bool(site.get("sponsor")),
                }
                for site in sites
            ],
            "products": [
                {
                    "categoryName": product.get("category_name") or "", "name": product.get("name") or "",
                    "price": product.get("price") or "", "priceNumber": float(product["price_number"]) if product.get("price_number") is not None else None,
                    "priceUnit": product.get("price_unit") or "", "inStock": bool(product.get("in_stock")),
                    "refreshedAt": str(product.get("sampled_at") or ""), "refreshTime": str(product.get("sampled_at") or ""),
                    "siteId": product.get("site_id") or "", "siteName": product.get("site_name") or "", "siteUrl": "",
                    "siteProductRefreshSuccessAt": str(product.get("sampled_at") or ""), "siteProductRefreshSuccessTime": str(product.get("sampled_at") or ""),
                    "siteScore": float(product.get("site_score") or 50), "siteSponsor": False, "clickCount": 0, "score": 0,
                    "standardProduct": product.get("standard_product") or "", "platform": product.get("platform") or "",
                    "productType": product.get("product_type") or "", "currencyCode": product.get("currency_code") or "CNY",
                    "sampledAt": str(product.get("sampled_at") or ""), "isSample": bool(product.get("is_sample")),
                    "sourceName": "", "sourcePageUrl": "", "sourcePriority": 0,
                }
                for product in products
            ],
            "totalSiteCount": len(sites),
            "totalProductCount": len(products),
            "totalInStockProductCount": sum(1 for product in products if product.get("in_stock")),
            "latestRefreshedAt": None,
            "latestRefreshTime": "",
            "isPartial": False,
        }
        repository.upsert_snapshot("shop-products", payload)

    def _rebuild_gateway_snapshot(self, repository) -> None:
        sites = repository.query("SELECT site_id, slug, name, host, family, score, sampled_at, is_sample, source_id, summary FROM gateway_sites")
        coverage = repository.query("SELECT site_id, model_id, model_family FROM gateway_model_coverage")
        by_site: dict[str, list[dict[str, Any]]] = {}
        for row in coverage:
            by_site.setdefault(str(row["site_id"]), []).append(row)
        payload = {
            "sites": [
                {
                    "id": site["site_id"], "slug": site.get("slug") or site["site_id"], "name": site.get("name") or "",
                    "url": "", "outboundUrl": "", "host": site.get("host") or "", "family": site.get("family") or "",
                    "displayFamily": site.get("family") or "", "createdAt": str(site.get("sampled_at") or ""),
                    "createdTime": str(site.get("sampled_at") or ""), "lastProductRefreshCompleteAt": None,
                    "lastProductRefreshCompleteTime": "", "siteScore": float(site.get("score") or 50), "sponsor": False,
                    "availabilityPercent": None, "avgSuccessLatencyMs": None, "summary": site.get("summary") or "",
                    "modelTypes": [], "paymentMethods": [],
                    "modelCount": len(by_site.get(str(site["site_id"]), [])), "priceCount": 0,
                    "modelFamilies": list({item.get("model_family") for item in by_site.get(str(site["site_id"]), []) if item.get("model_family")}),
                    "displayModelFamilies": list({item.get("model_family") for item in by_site.get(str(site["site_id"]), []) if item.get("model_family")}),
                    "refreshStatus": "", "refreshErrorType": "",
                    "latestGatewayRefreshAt": str(site.get("sampled_at") or ""),
                    "latestGatewayRefreshTime": str(site.get("sampled_at") or ""),
                    "sampledAt": str(site.get("sampled_at") or ""), "isSample": bool(site.get("is_sample")),
                    "sourceName": "", "sourcePageUrl": "",
                }
                for site in sites
            ],
            "totalSiteCount": len(sites),
            "sitesWithPricesCount": 0,
            "totalModelCount": len({item.get("model_id") for item in coverage}),
            "totalPriceCount": 0,
        }
        models = {}
        for item in coverage:
            models.setdefault(item["model_id"], {"id": item["model_id"], "modelId": item["model_id"], "modelFamily": item.get("model_family") or "Other", "supportSiteCount": 0, "priceCount": 0, "latestGatewayRefreshAt": None, "latestGatewayRefreshTime": ""})
            models[item["model_id"]]["supportSiteCount"] += 1
        repository.upsert_snapshot("gateway-sites", payload)
        repository.upsert_snapshot("gateway-models", {"models": list(models.values()), "totalModelCount": len(models), "totalSupportCount": sum(model["supportSiteCount"] for model in models.values())})

    def _rebuild_official_snapshot(self, repository) -> None:
        prices = repository.query("SELECT app_slug, plan_slug, app_name, plan_name, display_name, url_slug, is_default, display_order, country_code, country_label, currency_code, price_text, price_value, cny_price, usd_price, rub_price, source_id, sampled_at, is_sample, fetched_at FROM official_prices")
        payload = [
            {
                "appSlug": row["app_slug"], "planSlug": row["plan_slug"], "appName": row["app_name"], "planName": row["plan_name"],
                "displayName": row["display_name"], "urlSlug": row["url_slug"], "isDefault": bool(row["is_default"]),
                "displayOrder": int(row["display_order"] or 0), "countryCode": row["country_code"], "countryLabel": row["country_label"],
                "currencyCode": row["currency_code"], "priceText": row["price_text"], "priceValue": float(row["price_value"] or 0),
                "cnyPrice": float(row["cny_price"] or 0), "usdPrice": float(row["usd_price"] or 0), "rubPrice": float(row["rub_price"] or 0),
                "sourceId": row.get("source_id") or "", "sourceName": "", "sourcePageUrl": "",
                "sampledAt": str(row.get("sampled_at") or ""), "isSample": bool(row.get("is_sample")), "fetchedAt": str(row.get("fetched_at") or ""),
            }
            for row in prices
        ]
        catalog = []
        seen = set()
        for row in payload:
            key = f"{row['appSlug']}:{row['planSlug']}"
            if key in seen:
                continue
            seen.add(key)
            catalog.append({k: row[k] for k in ("appSlug", "planSlug", "appName", "planName", "displayName", "urlSlug", "isDefault", "displayOrder")})
        repository.upsert_snapshot("official-prices", payload)
        repository.upsert_snapshot("official-price-catalog", catalog)

    def _rebuild_rank_snapshot(self, repository) -> None:
        rows = repository.query("SELECT task_slug, source_name, source_url, source_group_slug, source_board_slug, rank, model_name, model_family, score, source_id, sampled_at, is_sample, fetched_at FROM model_leaderboards ORDER BY rank ASC")
        payload = [
            {
                "taskSlug": row["task_slug"], "sourceName": row.get("source_name") or "", "sourceUrl": row.get("source_url") or "",
                "sourceGroupSlug": row.get("source_group_slug") or "", "sourceBoardSlug": row.get("source_board_slug") or "",
                "rank": int(row.get("rank") or 0), "modelName": row.get("model_name") or "", "modelFamily": row.get("model_family") or "",
                "score": float(row.get("score") or 0), "sourceId": row.get("source_id") or "", "sampledAt": str(row.get("sampled_at") or ""),
                "isSample": bool(row.get("is_sample")), "fetchedAt": str(row.get("fetched_at") or ""),
            }
            for row in rows
        ]
        slugs = []
        for row in payload:
            if row["taskSlug"] not in slugs:
                slugs.append(row["taskSlug"])
        for extra in ("coding", "creative-writing", "math", "text-to-image", "video-generation"):
            if extra not in slugs:
                slugs.append(extra)
        repository.upsert_snapshot("model-leaderboards", payload)
        repository.upsert_snapshot("model-leaderboard-task-slugs", slugs)
