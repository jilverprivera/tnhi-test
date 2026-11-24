"""Adapter: background worker thread that drains the import queue."""

import logging
import threading

from app.features.ingestion.application.import_jobs import ProcessNextImport

log = logging.getLogger("docket.worker")


class ImportWorker:
    def __init__(self, process_next: ProcessNextImport, poll_seconds: float):
        self._process_next, self._poll = process_next, poll_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.alive:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="docket-import-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if self._process_next() is None:
                    self._stop.wait(self._poll)
            except Exception:
                log.exception("import worker iteration failed")
                self._stop.wait(self._poll)
