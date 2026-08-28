"""Dedupe by normalized site name; higher class wins; same class/priority keeps the lowest price."""
from __future__ import annotations

from typing import Any

from .config import source_class_rank


def _price(row: dict[str, Any]) -> float:
    try:
        return float(row.get("price"))
    except (TypeError, ValueError):
        return float("inf")


def merge_observations(rows: list[dict[str, Any]], sources_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        site = str(row.get("normalized_site") or "").strip().lower()
        if not site:
            continue
        grouped.setdefault(site, []).append(row)

    merged: list[dict[str, Any]] = []
    for site, candidates in grouped.items():
        ranked = sorted(
            candidates,
            key=lambda row: (
                -source_class_rank(sources_by_id.get(str(row.get("source_id")), {}))[0],
                -source_class_rank(sources_by_id.get(str(row.get("source_id")), {}))[1],
                -int(sources_by_id.get(str(row.get("source_id")), {}).get("priority") or row.get("source_priority") or 0),
                _price(row),
            ),
        )
        winner = dict(ranked[0])
        winner_source = sources_by_id.get(str(winner.get("source_id")), {})
        winner_rank = source_class_rank(winner_source)
        for extra in ranked[1:]:
            extra_source = sources_by_id.get(str(extra.get("source_id")), {})
            extra_rank = source_class_rank(extra_source)
            extra_priority = int(extra_source.get("priority") or extra.get("source_priority") or 0)
            winner_priority = int(winner_source.get("priority") or winner.get("source_priority") or 0)
            same_level = extra_rank[:2] == winner_rank[:2] and extra_priority == winner_priority
            if same_level and _price(extra) < _price(winner):
                winner = dict(extra)
                winner_source = extra_source
                winner_rank = extra_rank
                continue
            if extra_rank > winner_rank or extra_priority > winner_priority:
                continue
            for key, value in extra.items():
                if winner.get(key) in (None, "", []):
                    winner[key] = value
        winner["normalized_site"] = site
        merged.append(winner)
    return sorted(merged, key=lambda row: str(row.get("normalized_site")))
