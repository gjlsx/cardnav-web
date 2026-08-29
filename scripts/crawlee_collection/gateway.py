"""Parse the approved PriceAI model catalog and CardNav gateway detail pages."""
from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from scripts.collection.collection_lib.pipeline import SourceCapture


CARDNAV_ORIGIN = "https://cardnav.xyz"
_DETAIL_PATH = re.compile(r"^/llm-gateway/([a-z0-9][a-z0-9-]{0,120})$")
_SPACE = re.compile(r"\s+")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def normalize_gateway_model_id(value: str) -> str:
    """Return the project-standard lowercase model id, e.g. GPT 5.6 Luna."""
    return _SPACE.sub("-", " ".join(value.strip().split()).casefold())


def is_allowed_cardnav_detail_url(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc.casefold() == "cardnav.xyz"
        and not parsed.query
        and not parsed.fragment
        and _DETAIL_PATH.fullmatch(parsed.path) is not None
    )


@dataclass(frozen=True)
class GatewayListing:
    slug: str
    detail_url: str
    host: str
    name: str
    summary: str
    score: float


class _MarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, object]] = []
        self._row: dict[str, object] | None = None
        self._cell: list[str] | None = None
        self._anchor: dict[str, object] | None = None
        self._heading: list[str] | None = None
        self.heading = ""
        self.description = ""
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "tr":
            self._row = {"cells": [], "anchors": []}
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag == "a" and self._row is not None:
            self._anchor = {"href": values.get("href", ""), "text": []}
            anchors = self._row["anchors"]
            assert isinstance(anchors, list)
            anchors.append(self._anchor)
        elif tag == "h1":
            self._heading = []
        elif tag == "meta" and values.get("name", "").casefold() == "description":
            self.description = _clean(values.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            cells = self._row["cells"]
            assert isinstance(cells, list)
            cells.append(_clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "a":
            self._anchor = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
            self._cell = None
            self._anchor = None
        elif tag == "h1" and self._heading is not None:
            self.heading = _clean(" ".join(self._heading))
            self._heading = None

    def handle_data(self, data: str) -> None:
        cleaned = _clean(data)
        if not cleaned:
            return
        self.text.append(cleaned)
        if self._cell is not None:
            self._cell.append(cleaned)
        if self._anchor is not None:
            anchor_text = self._anchor["text"]
            assert isinstance(anchor_text, list)
            anchor_text.append(cleaned)
        if self._heading is not None:
            self._heading.append(cleaned)


def _clean(value: str) -> str:
    return _SPACE.sub(" ", value).strip()


def _parse(html: str) -> _MarkupParser:
    parser = _MarkupParser()
    parser.feed(html)
    return parser


def _first_line(value: str) -> str:
    return _clean(value.split("\n", 1)[0])


def _number_or_none(value: str) -> float | None:
    match = _NUMBER.search(value.replace(",", ""))
    return float(match.group(0)) if match else None


def _family(model_id: str) -> str:
    prefix = model_id.split("-", 1)[0]
    return {"gpt": "GPT", "claude": "Claude", "gemini": "Gemini", "grok": "Grok", "glm": "GLM", "deepseek": "DeepSeek", "kimi": "Kimi", "qwen": "Qwen"}.get(prefix, "Other")


def parse_priceai_standard_models(html: str) -> set[str]:
    """Read model labels from PriceAI's standard-model comparison table."""
    models: set[str] = set()
    for row in _parse(html).rows:
        cells = row["cells"]
        assert isinstance(cells, list)
        if not cells:
            continue
        cell_text = _clean(str(cells[0]))
        label_match = re.match(r"(.+?)\s+(?:ChatGPT|Claude|Gemini|Grok|GLM|DeepSeek|Kimi|千问|图片生成|视频生成)\s*·", cell_text)
        label = _clean(label_match.group(1)) if label_match else _first_line(cell_text)
        model_id = normalize_gateway_model_id(label)
        if model_id and model_id not in {"标准模型", "模型"}:
            models.add(model_id)
    return models


def discover_gateway_listings(html: str) -> list[GatewayListing]:
    """Discover only CardNav's directly rendered one-level gateway detail pages."""
    listings: dict[str, GatewayListing] = {}
    for row in _parse(html).rows:
        anchors = row["anchors"]
        cells = row["cells"]
        assert isinstance(anchors, list) and isinstance(cells, list)
        detail = None
        external = ""
        for anchor in anchors:
            href = urljoin(CARDNAV_ORIGIN, str(anchor.get("href") or ""))
            if is_allowed_cardnav_detail_url(href):
                detail = (href, _clean(" ".join(anchor.get("text") or [])))
            elif urlsplit(href).scheme == "https" and urlsplit(href).netloc.casefold() != "cardnav.xyz":
                external = href
        if detail is None or not external or len(cells) < 3:
            continue
        parsed = urlsplit(external)
        if not parsed.hostname:
            continue
        slug_match = _DETAIL_PATH.fullmatch(urlsplit(detail[0]).path)
        if slug_match is None:
            continue
        name = detail[1]
        cell_text = str(cells[1]) if len(cells) > 1 else ""
        summary = _clean(cell_text.replace(name, "", 1).replace(external, "").replace("详情", "").replace("打开", ""))
        score = _number_or_none(str(cells[2]))
        if score is None:
            continue
        listing = GatewayListing(slug_match.group(1), detail[0], parsed.hostname.casefold(), name, summary, score)
        listings.setdefault(listing.slug, listing)
    return list(listings.values())


def _metric(text: str, label: str, multiplier: float = 1.0) -> float | None:
    match = re.search(rf"{re.escape(label)}\s*[:：]?\s*(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) * multiplier if match else None


def parse_cardnav_gateway_detail(
    listing: GatewayListing,
    html: str,
    *,
    allowed_models: set[str],
    observed_at: str,
) -> dict[str, object]:
    """Map one public detail page to a single gateway raw record with model price metadata."""
    parser = _parse(html)
    models: list[dict[str, object]] = []
    for row in parser.rows:
        cells = row["cells"]
        assert isinstance(cells, list)
        if len(cells) < 7 or not str(cells[0]).strip().isdigit():
            continue
        model_id = normalize_gateway_model_id(str(cells[1]))
        if model_id not in allowed_models:
            continue
        models.append(
            {
                "model_id": model_id,
                "model_family": _family(model_id),
                "billing_unit": _clean(str(cells[2])),
                "input_price": _number_or_none(str(cells[3])),
                "output_price": _number_or_none(str(cells[4])),
                "cache_input_price": _number_or_none(str(cells[5])),
                "cache_output_price": _number_or_none(str(cells[6])),
            }
        )
    deduped = {str(model["model_id"]): model for model in models}
    page_text = " ".join(parser.text)
    availability = _metric(page_text, "可访问性")
    latency_seconds = _metric(page_text, "平均响应")
    return {
        "normalized_site": listing.host,
        "site_name": parser.heading or listing.name,
        "display_name": parser.heading or listing.name,
        "url": f"https://{listing.host}",
        "summary": listing.summary or parser.description,
        "observed_at": observed_at,
        "provenance": "cardnav-browser",
        "metadata_json": {
            "site_score": listing.score,
            "availability_percent": availability,
            "avg_success_latency_ms": int(latency_seconds * 1000) if latency_seconds is not None else None,
            "models": list(deduped.values()),
        },
    }


def _source_mapping(source) -> dict[str, object]:  # noqa: ANN001
    return {
        "id": source.source_id,
        "name": source.name,
        "source_class": source.source_class,
        "priority": source.priority,
        "public_url": source.url,
    }


def build_cardnav_captures(
    model_source,
    model_html: str,
    list_source,
    list_html: str,
    detail_pages: dict[str, str],
    *,
    observed_at: str,
) -> list[SourceCapture]:  # noqa: ANN001
    """Build raw-only captures; model catalog and list are audit payloads, details are records."""
    allowed_models = parse_priceai_standard_models(model_html)
    captures = [
        SourceCapture(source=_source_mapping(model_source), body=model_html, rows=[], content_type="text/html", kind=model_source.record_kind),
        SourceCapture(source=_source_mapping(list_source), body=list_html, rows=[], content_type="text/html", kind=list_source.record_kind),
    ]
    for listing in discover_gateway_listings(list_html):
        html = detail_pages.get(listing.detail_url)
        if html is None:
            continue
        row = parse_cardnav_gateway_detail(listing, html, allowed_models=allowed_models, observed_at=observed_at)
        captures.append(SourceCapture(source=_source_mapping(list_source), body=html, rows=[row], content_type="text/html", kind=list_source.record_kind))
    return captures
