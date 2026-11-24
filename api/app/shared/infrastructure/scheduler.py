"""A small periodic task runner (background thread) for housekeeping jobs such as the Excel sync."""

import logging
import threading
from collections.abc import Callable

log = logging.getLogger("docket.scheduler")


class PeriodicTask:
    def __init__(self, name: str, task: Callable[[], object], every_seconds: float | None):
        self._name, self._task, self._every = name, task, every_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.alive or not self._every or self._every <= 0:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"docket-{self._name}", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.wait(self._every):
            try:
                self._task()
            except Exception:
                log.exception("periodic task %s failed", self._name)
