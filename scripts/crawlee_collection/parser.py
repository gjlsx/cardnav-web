"""Page-type parsers that turn PriceAI browser HTML into existing raw contracts."""
from __future__ import annotations

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


def parse_priceai_page(source: BrowserSource, html: str, *, observed_at: str) -> SourceCapture:
    """Parse only explicit card markup for the matching allowlisted PriceAI page type."""
    parser = _CollectionCardParser()
    parser.feed(html)
    parsers = {
        "card_subscriptions": ("shop", _parse_shop),
        "official_api": ("official", _parse_official),
        "transit_api": ("gateway", _parse_gateway),
    }
    expected_card_type, parse_card = parsers[source.page_type]
    rows = [row for card in parser.cards if card["type"] == expected_card_type for row in [parse_card(card, observed_at)] if row]
    return SourceCapture(source=_source_mapping(source), body=html, rows=rows, content_type="text/html", kind=source.record_kind)
