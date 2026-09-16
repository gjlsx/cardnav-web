"""Reusable MySQL facade over the existing collection repository and importer."""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from scripts.collection.collection_lib.repository import CollectionRepository, open_local_connection
from scripts.collection.collection_lib.runtime_import import RuntimeImporter

DEFAULT_IDLE_TTL_S = 600
T = TypeVar("T")


class ReusableRepository:
    """Keep one MySQL session for an active CLI/worker window, then close on idle or error."""

    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
        idle_ttl_s: int = DEFAULT_IDLE_TTL_S,
        clock: Callable[[], float] | None = None,
        importer: RuntimeImporter | None = None,
    ) -> None:
        self.connection_factory = connection_factory or open_local_connection
        self.idle_ttl_s = idle_ttl_s
        self.clock = clock or time.monotonic
        self.importer = importer or RuntimeImporter()
        self._connection: Any | None = None
        self._repository: CollectionRepository | None = None
        self._last_used: float | None = None

    def repository(self) -> CollectionRepository:
        self.close_if_idle()
        if self._repository is not None and not self._connection_usable():
            self._close_current()
        if self._repository is None:
            self._connection = self.connection_factory()
            self._repository = CollectionRepository(self._connection)
        self._last_used = self.clock()
        return self._repository

    def close_if_idle(self) -> bool:
        if self._repository is None or self._last_used is None:
            return False
        if self.clock() - self._last_used < self.idle_ttl_s:
            return False
        self._close_current()
        return True

    def run_in_transaction(self, work: Callable[[CollectionRepository], T]) -> T:
        repository = self.repository()
        try:
            result = work(repository)
            repository.commit()
            return result
        except Exception:
            repository.rollback()
            raise

    def ready_batch_ids(self, source_id: str | None = None) -> list[str]:
        if source_id:
            rows = self.repository().query(
                "SELECT DISTINCT batch.batch_id FROM collection_batches batch "
                "JOIN collection_raw_records raw ON raw.batch_id = batch.batch_id "
                "WHERE batch.status = %s AND raw.source_id = %s "
                "ORDER BY batch.started_at ASC, batch.batch_id ASC",
                ("raw_completed", source_id),
            )
        else:
            rows = self.repository().query(
                "SELECT batch_id FROM collection_batches WHERE status = %s ORDER BY started_at ASC, batch_id ASC",
                ("raw_completed",),
            )
        return [str(row["batch_id"]) for row in rows]

    def merge_batch(self, batch_id: str) -> dict[str, Any]:
        return self.importer.merge_import_batch(self.repository(), batch_id)

    def persist_captures(self, captures: list[Any], trigger: str = "manual") -> dict[str, Any]:
        from scripts.collection.collection_lib.migrations import apply_migrations
        from scripts.collection.collection_lib.pipeline import run_collection_batch

        repository = self.repository()
        apply_migrations(repository.connection)
        return run_collection_batch(repository, captures, trigger=trigger)

    def list_raw_batches(self) -> list[dict[str, Any]]:
        return self.repository().query(
            "SELECT batch.batch_id, batch.status, batch.started_at, COUNT(raw.id) AS raw_count "
            "FROM collection_batches batch LEFT JOIN collection_raw_records raw ON raw.batch_id = batch.batch_id "
            "GROUP BY batch.batch_id, batch.status, batch.started_at "
            "ORDER BY batch.started_at DESC"
        )

    def _connection_usable(self) -> bool:
        connection = self._connection
        if connection is None or getattr(connection, "closed", False):
            return False
        ping = getattr(connection, "ping", None)
        if ping is None:
            return True
        try:
            ping(reconnect=False)
            return True
        except Exception:
            return False

    def _close_current(self) -> None:
        connection = self._connection
        self._connection = None
        self._repository = None
        self._last_used = None
        if connection is None:
            return
        closer = getattr(connection, "close", None)
        if closer is not None:
            closer()
