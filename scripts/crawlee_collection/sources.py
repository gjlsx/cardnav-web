"""Fixed source registry for the independent browser collector."""
from __future__ import annotations

from dataclasses import dataclass

from scripts.collection.collection_lib.contracts import RecordKind


MAX_CONCURRENCY = 1
PRICEAI_SOURCE_IDS = (
    "priceai-card-subscriptions",
    "priceai-official-api",
    "priceai-transit-api",
    "priceai-transit-models",
    "cardnav-gateway-details",
)


@dataclass(frozen=True)
class BrowserSource:
    source_id: str
    name: str
    url: str
    page_type: str
    record_kind: RecordKind
    source_class: str = "aggregator"
    priority: int = 0
    enabled: bool = False


_SOURCES = (
    BrowserSource(
        "priceai-card-subscriptions",
        "PriceAI 卡网订阅",
        "https://priceai.cc/channels",
        "card_subscriptions",
        RecordKind.SHOP_PRODUCT,
    ),
    BrowserSource(
        "priceai-official-api",
        "PriceAI 官方 API",
        "https://priceai.cc/official-api",
        "official_api",
        RecordKind.OFFICIAL_PLAN,
    ),
    BrowserSource(
        "priceai-transit-api",
        "PriceAI 中转 API",
        "https://priceai.cc/api-transit",
        "transit_api",
        RecordKind.GATEWAY_SITE,
    ),
    BrowserSource(
        "priceai-transit-models",
        "PriceAI 中转标准模型",
        "https://priceai.cc/api-transit/models",
        "transit_model_catalog",
        RecordKind.GATEWAY_SITE,
    ),
    BrowserSource(
        "cardnav-gateway-details",
        "CardNav 中转站详情",
        "https://cardnav.xyz/llm-gateway",
        "cardnav_gateway_details",
        RecordKind.GATEWAY_SITE,
    ),
)
_BY_ID = {source.source_id: source for source in _SOURCES}


def list_sources() -> tuple[BrowserSource, ...]:
    """Return the allowlisted sources in their fixed collection order."""
    return _SOURCES


def get_source(source_id: str) -> BrowserSource:
    try:
        return _BY_ID[source_id]
    except KeyError as exc:
        raise ValueError(f"unknown source: {source_id}") from exc


def require_allowed_source(source_id: str, url: str) -> BrowserSource:
    """Reject arbitrary URLs and return the matching, exact source entry."""
    source = get_source(source_id)
    if url != source.url:
        raise ValueError(f"URL is not allowed for {source_id}: {url}")
    return source
