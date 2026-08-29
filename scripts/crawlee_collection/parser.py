"""Page-type parsers that turn PriceAI browser HTML into existing raw contracts."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit

from scripts.collection.collection_lib.pipeline import SourceCapture

from .sources import BrowserSource


_PRICE_RE = re.compile(r"([¥￥$])\s*([0-9]+(?:\.[0-9]+)?)")
_SPACE_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_SHOP_SUFFIX_RE = re.compile(r"\s*(月卡|年卡|季卡|周卡|订阅|套餐)\s*$", re.IGNORECASE)
_FAMILY_PLAN_RE = re.compile(
    r"(ChatGPT|Claude|Gemini|Grok)[\s\S]{0,120}?(Free|Go|Plus|Pro 20x|Pro 5x|Pro|Max 20x|Max 5x|Max)\s*\$([0-9]+(?:\.[0-9]+)?)\s*/月",
    re.IGNORECASE,
)
_SKIP_HOSTS = ("priceai.cc", "stripe.com", "twitter.com", "facebook.com", "google.com", "cloudflare.com")


class _CollectionCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, Any]] = []
        self._card: dict[str, Any] | None = None
        self._tag_stack: list[str] = []
        self._anchor_text: list[str] | None = None
        self._heading_text: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "article" and values.get("data-collection-card"):
            self._card = {"type": values["data-collection-card"], "country": values.get("data-country", ""), "text": [], "anchors": [], "headings": []}
        if self._card is None:
            return
        self._tag_stack.append(tag)
        if tag == "a":
            self._anchor_text = []
            self._card["anchors"].append({"href": values.get("href", ""), "text": self._anchor_text})
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading_text = []
            self._card["headings"].append(self._heading_text)

    def handle_endtag(self, tag: str) -> None:
        if self._card is None:
            return
        if self._tag_stack:
            self._tag_stack.pop()
        if tag == "a":
            self._anchor_text = None
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading_text = None
        if tag == "article":
            self.cards.append(self._card)
            self._card = None
            self._anchor_text = None
            self._heading_text = None

    def handle_data(self, data: str) -> None:
        if self._card is None:
            return
        text = _clean_text(data)
        if not text:
            return
        self._card["text"].append(text)
        if self._anchor_text is not None:
            self._anchor_text.append(text)
        if self._heading_text is not None:
            self._heading_text.append(text)


def _clean_text(value: str) -> str:
    return _SPACE_RE.sub(" ", value).strip()


def _slug(value: str) -> str:
    return _SLUG_RE.sub("-", value.casefold()).strip("-")


def _first_heading(card: dict[str, Any]) -> str:
    for parts in card["headings"]:
        value = _clean_text(" ".join(parts))
        if value:
            return value
    return ""


def _first_anchor(card: dict[str, Any]) -> tuple[str, str]:
    for anchor in card["anchors"]:
        href = str(anchor["href"])
        host = urlsplit(href).hostname
        if host:
            return host.casefold(), _clean_text(" ".join(anchor["text"]))
    return "", ""


def _price_fields(text: str) -> dict[str, Any]:
    match = _PRICE_RE.search(text)
    if not match:
        return {"price": None, "currency": None}
    return {"price": float(match.group(2)), "currency": "CNY" if match.group(1) in {"¥", "￥"} else "USD"}


def _source_mapping(source: BrowserSource) -> dict[str, Any]:
    return {
        "id": source.source_id,
        "name": source.name,
        "source_class": source.source_class,
        "priority": source.priority,
        "public_url": source.url,
    }


def _parse_shop(card: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    host, anchor_name = _first_anchor(card)
    heading = _first_heading(card)
    sku = _slug(_SHOP_SUFFIX_RE.sub("", heading))
    if not host or not sku:
        return None
    text = " ".join(card["text"])
    return {
        "normalized_site": host,
        "site_name": anchor_name or host,
        "canonical_sku": sku,
        "model_or_plan": heading,
        "display_name": heading,
        "stock_status": "out_of_stock" if "缺货" in text else "in_stock",
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        **_price_fields(text),
    }


def _parse_official(card: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    plan = _first_heading(card)
    country = str(card.get("country") or "").strip().upper()
    if not plan or not country or len(country) != 2:
        return None
    text = " ".join(card["text"])
    return {
        "plan_slug": _slug(plan),
        "model_or_plan": plan,
        "display_name": plan,
        "country_code": country,
        "region": country,
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        **_price_fields(text),
    }


def _parse_gateway(card: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    host, anchor_name = _first_anchor(card)
    heading = _first_heading(card)
    if not host:
        return None
    text = " ".join(card["text"])
    return {
        "normalized_site": host,
        "site_name": heading or anchor_name or host,
        "display_name": heading or anchor_name or host,
        "model_or_plan": text,
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        **_price_fields(text),
    }


def _skip_host(host: str) -> bool:
    lowered = host.casefold()
    return any(part in lowered for part in _SKIP_HOSTS)


def _decode_embedded(html: str) -> str:
    return html.replace('\\"', '"').replace("\\u0022", '"')


def _json_objects(html: str) -> list[dict[str, Any]]:
    text = _decode_embedded(html)
    objects: list[dict[str, Any]] = []
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        for index, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blob = text[start : index + 1]
                    if 20 < len(blob) < 8000:
                        try:
                            payload = json.loads(blob)
                        except json.JSONDecodeError:
                            payload = None
                        if isinstance(payload, dict):
                            objects.append(payload)
                    break
        if len(objects) >= 400:
            break
    return objects


def _parse_shop_listing(payload: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    url = str(payload.get("url") or "")
    host = urlsplit(url).hostname
    title = str(payload.get("sourceTitle") or "")
    store = str(payload.get("sourceStoreName") or payload.get("sourceName") or "")
    if not host or not title or not store or _skip_host(host):
        return None
    sku = _slug(_SHOP_SUFFIX_RE.sub("", title))
    if not sku:
        return None
    status = str(payload.get("status") or "").casefold()
    return {
        "normalized_site": host.casefold(),
        "site_name": store,
        "canonical_sku": sku,
        "model_or_plan": title,
        "display_name": title,
        "stock_status": "out_of_stock" if status in {"out_of_stock", "缺货"} else "in_stock",
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        "price": float(payload["price"]) if payload.get("price") is not None else None,
        "currency": payload.get("currency") or ("CNY" if payload.get("price") is not None else None),
    }


def _parse_official_listing(payload: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    if str(payload.get("type") or "").casefold() != "official":
        return None
    name = str(payload.get("name") or payload.get("id") or "")
    slug = _slug(str(payload.get("id") or name))
    if not name or not slug:
        return None
    return {
        "plan_slug": slug,
        "model_or_plan": name,
        "display_name": name,
        "country_code": "US",
        "region": "US",
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        "price": None,
        "currency": None,
    }


def _parse_official_plans(html: str, observed_at: str) -> list[dict[str, Any]]:
    rows = []
    for match in _FAMILY_PLAN_RE.finditer(html):
        family, plan, amount = match.group(1), match.group(2), match.group(3)
        rows.append(
            {
                "plan_slug": _slug(f"{family} {plan}"),
                "model_or_plan": f"{family} {plan}",
                "display_name": f"{family} {plan}",
                "country_code": "US",
                "region": "US",
                "observed_at": observed_at,
                "provenance": "priceai-browser",
                "price": float(amount),
                "currency": "USD",
            }
        )
    return rows


def _parse_gateway_listing(payload: dict[str, Any], observed_at: str) -> dict[str, Any] | None:
    if payload.get("sourceStoreName") or str(payload.get("type") or "").casefold() == "official":
        return None
    url = str(payload.get("url") or payload.get("homepage") or "")
    host = urlsplit(url).hostname
    name = str(payload.get("siteName") or payload.get("name") or "")
    if not host or not name or _skip_host(host):
        return None
    return {
        "normalized_site": host.casefold(),
        "site_name": name,
        "display_name": name,
        "model_or_plan": name,
        "observed_at": observed_at,
        "provenance": "priceai-browser",
        "price": float(payload["price"]) if isinstance(payload.get("price"), (int, float)) else None,
        "currency": None,
    }


def _unique_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (str(row.get("normalized_site") or row.get("plan_slug") or ""), str(row.get("canonical_sku") or row.get("country_code") or row.get("site_name") or ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def _parse_live_rows(source: BrowserSource, html: str, observed_at: str) -> list[dict[str, Any]]:
    objects = _json_objects(html)
    if source.page_type == "card_subscriptions":
        return _unique_rows(row for payload in objects for row in [_parse_shop_listing(payload, observed_at)] if row)
    if source.page_type == "official_api":
        rows = [row for payload in objects for row in [_parse_official_listing(payload, observed_at)] if row]
        rows.extend(_parse_official_plans(html, observed_at))
        return _unique_rows(rows)
    return _unique_rows(row for payload in objects for row in [_parse_gateway_listing(payload, observed_at)] if row)


def parse_priceai_page(source: BrowserSource, html: str, *, observed_at: str) -> SourceCapture:
    """Parse allowlisted PriceAI markup or embedded public listings into existing contracts."""
    parser = _CollectionCardParser()
    parser.feed(html)
    parsers = {
        "card_subscriptions": ("shop", _parse_shop),
        "official_api": ("official", _parse_official),
        "transit_api": ("gateway", _parse_gateway),
    }
    expected_card_type, parse_card = parsers[source.page_type]
    rows = [row for card in parser.cards if card["type"] == expected_card_type for row in [parse_card(card, observed_at)] if row]
    if not rows:
        rows = _parse_live_rows(source, html, observed_at)
    return SourceCapture(source=_source_mapping(source), body=html, rows=rows, content_type="text/html", kind=source.record_kind)
