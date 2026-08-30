"""Map the small GUI buttons onto the same CLI argv used on Linux."""
from __future__ import annotations

import sys

MODULE_TABS = (
    ("collect", "采集", ("collect-once", "collect", "collect-stop")),
    ("merge", "入库", ("merge", "merge-stop")),
)

SOURCE_SHORT_LABELS = {
    "priceai-card-subscriptions": "卡网",
    "priceai-official-api": "官方",
    "priceai-transit-api": "中转",
    "cardnav-gateway-details": "中转",
    "hvoyai-awesome-ai-api": "参考",
}

_START_PREFIX = {"collect": "采集", "merge": "入库"}


def button_label(action: str, source_id: str) -> str:
    short = SOURCE_SHORT_LABELS[source_id]
    if action.endswith("-stop"):
        return f"停止{short}"
    if action == "collect-once":
        return f"抓取一次{short}"
    return f"{_START_PREFIX[action]}{short}"


def cli_argv(action: str, source_id: str) -> list[str]:
    if action == "collect-once":
        return [sys.executable, "-m", "scripts.crawlee_collection", "collect", "--source", source_id]
    if action == "collect":
        return [sys.executable, "-m", "scripts.crawlee_collection", "collect", "--source", source_id, "--loop"]
    if action == "merge":
        return [sys.executable, "-m", "scripts.crawlee_collection", "worker", "--source", source_id, "--loop"]
    if action == "collect-stop":
        return ["stop", "collect", source_id]
    if action == "merge-stop":
        return ["stop", "merge", source_id]
    raise ValueError(f"unknown gui action: {action}")
