"""Default-off singleton merge/import worker. It never performs browser collection."""
from __future__ import annotations

from typing import Any, Protocol

WORKER_POLL_INTERVAL_S = 10


class MergeStorage(Protocol):
    def ready_batch_ids(self) -> list[str]: ...

    def merge_batch(self, batch_id: str) -> dict[str, Any]: ...

    def close_if_idle(self) -> bool: ...


class MergeImportWorker:
    _running: MergeImportWorker | None = None

    def __init__(self, storage: MergeStorage, poll_interval_s: int = WORKER_POLL_INTERVAL_S) -> None:
        self.storage = storage
        self.poll_interval_s = poll_interval_s
        self.is_running = False

    @classmethod
    def reset(cls) -> None:
        if cls._running is not None:
            cls._running.is_running = False
        cls._running = None

    def start(self) -> None:
        if MergeImportWorker._running is not None:
            raise RuntimeError("merge/import worker already running")
        self.is_running = True
        MergeImportWorker._running = self

    def stop(self) -> None:
        if MergeImportWorker._running is self:
            MergeImportWorker._running = None
        self.is_running = False

    def run_once(self) -> list[dict[str, Any]]:
        results = [self.storage.merge_batch(batch_id) for batch_id in self.storage.ready_batch_ids()]
        self.storage.close_if_idle()
        return results
