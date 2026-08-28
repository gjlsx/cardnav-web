"""Allowed staging fields. Full HTML, cookies, accounts, and order details are rejected."""

ALLOWED_FIELDS = (
    "normalized_site",
    "source_id",
    "source_class",
    "source_priority",
    "platform_family",
    "model_or_plan",
    "price",
    "currency",
    "billing_unit",
    "stock_status",
    "region",
    "payment_tags",
    "delivery_tags",
    "public_perf",
    "observed_at",
    "provenance",
    "confidence",
    "canonical_sku",
    "product_type",
    "display_name",
    "channel_count",
    "available_channel_count",
    "out_of_stock_channel_count",
    "site_name",
    "summary",
    "model_family",
    "model_name",
    "task_slug",
    "plan_slug",
    "country_code",
    "rank",
    "url",
)

FORBIDDEN_FIELD_MARKERS = (
    "html",
    "cookie",
    "authorization",
    "password",
    "account",
    "order",
    "delivery_detail",
    "body",
)


def filter_observation(raw: dict) -> dict:
    cleaned = {}
    for key, value in raw.items():
        lowered = str(key).strip().lower()
        if lowered in FORBIDDEN_FIELD_MARKERS:
            continue
        if lowered not in ALLOWED_FIELDS:
            continue
        cleaned[lowered] = value
    return cleaned
