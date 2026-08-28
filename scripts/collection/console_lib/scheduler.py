"""In-process per-source scheduler. Stops when the GUI process exits."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable


class LocalScheduler:
    def __init__(self, after, run_source: Callable[[dict[str, Any]], Any]):
        self._after = after
        self._run_source = run_source
        self.enabled = False
        self.next_due: dict[str, datetime] = {}
        self._job = None
        self.running: set[str] = set()

    def start(self) -> None:
        self.enabled = True
        self._tick()

    def stop(self) -> None:
        self.enabled = False

    def due_sources(self, sources: list[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or datetime.now(timezone.utc)
        due = []
        for source in sources:
            if not source.get("enabled"):
                continue
            source_id = source["id"]
            nxt = self.next_due.get(source_id)
            if nxt and nxt > now:
                continue
            due.append(source)
        return due

    def mark_ran(self, source: dict[str, Any], now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        minutes = max(1, int(source.get("interval_minutes") or 60))
        self.next_due[source["id"]] = now + timedelta(minutes=minutes)
        self.running.discard(source["id"])

    def _tick(self) -> None:
        if not self.enabled:
            return
        # GUI supplies sources via run_source side effects; tick only reschedules.
        self._after(30000, self._tick)
