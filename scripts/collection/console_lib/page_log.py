"""Per-page log buffers that never mix Tab output."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone


class PageLogs:
    def __init__(self):
        self._lines: dict[str, list[str]] = defaultdict(list)

    def append(self, page_key: str, message: str) -> str:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        self._lines[page_key].append(line)
        return line

    def text(self, page_key: str) -> str:
        return "\n".join(self._lines[page_key])

    def keys(self) -> list[str]:
        return list(self._lines)
