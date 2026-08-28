"""Thread-safe source-level run and stop flags for the desktop console."""
from __future__ import annotations

import threading


class SourceRunControl:
    def __init__(self):
        self._flags: dict[str, threading.Event] = {}
        self._loops: set[str] = set()
        self._running: set[str] = set()
        self._lock = threading.Lock()

    def start_loop(self, source_id: str) -> threading.Event:
        with self._lock:
            flag = threading.Event()
            self._flags[source_id] = flag
            self._loops.add(source_id)
            return flag

    def begin(self, source_id: str) -> threading.Event | None:
        with self._lock:
            if source_id in self._running:
                return None
            flag = self._flags.get(source_id)
            if flag is None or flag.is_set():
                flag = threading.Event()
                self._flags[source_id] = flag
            self._running.add(source_id)
            return flag

    def finish(self, source_id: str) -> None:
        with self._lock:
            self._running.discard(source_id)

    def stop(self, source_id: str) -> str:
        with self._lock:
            self._loops.discard(source_id)
            self._flags.setdefault(source_id, threading.Event()).set()
        return f"task {source_id} is stop!"

    def is_looping(self, source_id: str) -> bool:
        with self._lock:
            return source_id in self._loops

    def should_stop(self, source_id: str) -> bool:
        with self._lock:
            return self._flags.get(source_id, threading.Event()).is_set()
