"""Bounded public JSON fetch for individually approved collection sources."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen


def fetch_approved_json(source: dict) -> tuple[str, list[dict], str]:
    if str(source.get("approval_status") or "").lower() != "approved":
        raise ValueError("source is not approved")
    url = str(source.get("public_url") or "")
    allowlist = list(source.get("allowlist_urls") or [])
    if not url or url not in allowlist:
        raise ValueError("public_url must be in allowlist_urls")
    request = Request(url, headers={"User-Agent": "AILoveMoney-Collector/1.0 (+https://ai.lovemoney.live)"})
    with urlopen(request, timeout=15) as response:  # noqa: S310 - URL is a user-approved exact allowlist member.
        body = response.read().decode("utf-8")
        content_type = response.headers.get_content_type()
    payload = json.loads(body)
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("approved response must be a JSON object list or {rows: [...]}")
    return body, rows, content_type
