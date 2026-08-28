"""Background task runner: worker threads emit events, Tk main thread applies them."""
from __future__ import annotations

import queue
import threading
from typing import Any, Callable


class TaskRunner:
    def __init__(self, after):
        self._after = after
        self._queue: queue.Queue[tuple[str, str, Any]] = queue.Queue()
        self.busy: set[str] = set()
        self._pumping = False

    def submit(self, action: str, fn: Callable[[], Any], on_event: Callable[[str, str, Any], None]) -> bool:
        if action in self.busy:
            on_event("busy", action, "already running")
            return False
        self.busy.add(action)
        on_event("start", action, None)

        def worker() -> None:
            try:
                result = fn()
                self._queue.put(("ok", action, result))
            except Exception as exc:  # noqa: BLE001
                self._queue.put(("err", action, str(exc)))
            finally:
                self._queue.put(("done", action, None))

        threading.Thread(target=worker, daemon=True).start()
        self._ensure_pump(on_event)
        return True

    def _ensure_pump(self, on_event: Callable[[str, str, Any], None]) -> None:
        if self._pumping:
            return
        self._pumping = True

        def pump() -> None:
            try:
                while True:
                    kind, action, payload = self._queue.get_nowait()
                    if kind == "done":
                        self.busy.discard(action)
                    on_event(kind, action, payload)
            except queue.Empty:
                pass
            if self.busy or not self._queue.empty():
                self._after(50, pump)
            else:
                self._pumping = False

        self._after(50, pump)
