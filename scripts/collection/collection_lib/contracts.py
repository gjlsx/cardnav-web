"""Immutable data contracts shared by collection, publishing, and the desktop console."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping
from urllib.parse import urlsplit


class RecordKind(str, Enum):
    SHOP_PRODUCT = "shop_product"
    GATEWAY_SITE = "gateway_site"
    OFFICIAL_PLAN = "official_plan"
    MODEL_RANK = "model_rank"


class OverrideState(str, Enum):
    MANUAL = "manual"
    HIDDEN = "hidden"


def normalize_host(value: str) -> str:
    """Return a canonical hostname without scheme, path, port, or case differences."""
    text = value.strip()
    if not text:
        raise ValueError("host is required")
    parsed = urlsplit(text if "://" in text or text.startswith("//") else f"//{text}")
    if not parsed.hostname:
        raise ValueError(f"invalid host: {value}")
    return parsed.hostname.casefold().rstrip(".")


def _slug(value: str, label: str) -> str:
    normalized = re.sub(r"[^\w]+", "-", value.strip().casefold(), flags=re.UNICODE).strip("-_")
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def record_key(kind: RecordKind, **identity: str) -> str:
    """Build the stable identity used for dedupe and manual overrides."""
    if kind is RecordKind.SHOP_PRODUCT:
        return f"{kind.value}:{normalize_host(identity.get('host', ''))}:{_slug(identity.get('canonical_sku', ''), 'canonical_sku')}"
    if kind is RecordKind.GATEWAY_SITE:
        return f"{kind.value}:{normalize_host(identity.get('host', ''))}"
    if kind is RecordKind.OFFICIAL_PLAN:
        return f"{kind.value}:{_slug(identity.get('plan_slug', ''), 'plan_slug')}:{_slug(identity.get('country_code', ''), 'country_code').upper()}"
    if kind is RecordKind.MODEL_RANK:
        return f"{kind.value}:{_slug(identity.get('task_slug', ''), 'task_slug')}:{_slug(identity.get('model_name', ''), 'model_name')}"
    raise ValueError(f"unsupported record kind: {kind}")


@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    name: str
    source_class: str
    target_domain: str
    priority: int = 0
    enabled: bool = False
    interval_minutes: int = 60
    max_items_per_run: int = 1000
    approval_status: str = "draft"
    field_whitelist: tuple[str, ...] = ()


@dataclass(frozen=True)
class CollectionRun:
    run_id: str
    source_id: str
    trigger: str
    started_at: str | None = None


@dataclass(frozen=True)
class RawPayload:
    run_id: str
    source_id: str
    body_hash: str
    content_type: str
    body: str | None = None


@dataclass(frozen=True)
class RawRecord:
    run_id: str
    source_id: str
    record_key: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class StagingRecord:
    run_id: str
    record_kind: RecordKind
    record_key: str
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class ManualOverride:
    record_kind: RecordKind
    record_key: str
    state: OverrideState
    payload: Mapping[str, Any] | None = None
