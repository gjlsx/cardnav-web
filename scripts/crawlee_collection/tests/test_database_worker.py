from __future__ import annotations

import unittest

from scripts.crawlee_collection.database import DEFAULT_IDLE_TTL_S, ReusableRepository
from scripts.crawlee_collection.worker import MergeImportWorker


class _Connection:
    def __init__(self) -> None:
        self.closed = False
        self.commits = 0
        self.rollbacks = 0
        self.ping_calls = 0
        self.fail_ping = False

    def ping(self, reconnect: bool = False) -> None:
        self.ping_calls += 1
        if self.closed or self.fail_ping:
            raise RuntimeError("connection lost")

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


class DatabaseFacadeTests(unittest.TestCase):
    def test_reuses_one_connection_until_idle_ttl_expires(self) -> None:
        connections: list[_Connection] = []
        now = [0.0]
        store = ReusableRepository(
            connection_factory=lambda: connections.append(_Connection()) or connections[-1],
            idle_ttl_s=DEFAULT_IDLE_TTL_S,
            clock=lambda: now[0],
        )

        first = store.repository()
        now[0] = 599.0
        self.assertIs(store.repository(), first)
        self.assertFalse(store.close_if_idle())
        now[0] = 1200.0
        self.assertTrue(store.close_if_idle())
        self.assertTrue(connections[0].closed)
        self.assertIsNot(store.repository(), first)
        self.assertEqual(len(connections), 2)

    def test_replaces_closed_or_broken_connection_before_reuse(self) -> None:
        connections: list[_Connection] = []
        store = ReusableRepository(
            connection_factory=lambda: connections.append(_Connection()) or connections[-1],
            idle_ttl_s=DEFAULT_IDLE_TTL_S,
            clock=lambda: 0.0,
        )

        first = store.repository()
        connections[0].fail_ping = True
        second = store.repository()
        self.assertIsNot(second, first)
        self.assertTrue(connections[0].closed)
        self.assertEqual(len(connections), 2)

        connections[1].close()
        third = store.repository()
        self.assertIsNot(third, second)
        self.assertEqual(len(connections), 3)

    def test_batch_work_commits_and_rolls_back_on_the_reused_connection(self) -> None:
        connections: list[_Connection] = []
        store = ReusableRepository(
            connection_factory=lambda: connections.append(_Connection()) or connections[-1],
            idle_ttl_s=DEFAULT_IDLE_TTL_S,
            clock=lambda: 0.0,
        )

        self.assertEqual(store.run_in_transaction(lambda repo: "ok"), "ok")
        self.assertEqual(connections[0].commits, 1)
        self.assertEqual(connections[0].rollbacks, 0)

        with self.assertRaisesRegex(RuntimeError, "boom"):
            store.run_in_transaction(_raise)
        self.assertEqual(connections[0].commits, 1)
        self.assertEqual(connections[0].rollbacks, 1)


def _raise(_repo: object) -> None:
    raise RuntimeError("boom")


class _Storage:
    def __init__(self) -> None:
        self.merged: list[str] = []

    def ready_batch_ids(self) -> list[str]:
        return ["batch-a", "batch-b"]

    def merge_batch(self, batch_id: str) -> dict[str, object]:
        self.merged.append(batch_id)
        return {"batch_id": batch_id, "runtime_writes": 1}

    def close_if_idle(self) -> bool:
        return False


class WorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        MergeImportWorker.reset()

    def tearDown(self) -> None:
        MergeImportWorker.reset()

    def test_run_once_merges_ready_batches_serially_without_auto_start(self) -> None:
        storage = _Storage()
        worker = MergeImportWorker(storage, poll_interval_s=10)

        self.assertFalse(worker.is_running)
        self.assertEqual(worker.poll_interval_s, 10)
        self.assertEqual(worker.run_once(), [{"batch_id": "batch-a", "runtime_writes": 1}, {"batch_id": "batch-b", "runtime_writes": 1}])
        self.assertEqual(storage.merged, ["batch-a", "batch-b"])
        self.assertFalse(worker.is_running)

    def test_only_one_worker_may_start_in_process(self) -> None:
        first = MergeImportWorker(_Storage(), poll_interval_s=10)
        second = MergeImportWorker(_Storage(), poll_interval_s=10)

        first.start()
        self.assertTrue(first.is_running)
        with self.assertRaisesRegex(RuntimeError, "already running"):
            second.start()
        first.stop()
        self.assertFalse(first.is_running)
        second.start()
        self.assertTrue(second.is_running)
