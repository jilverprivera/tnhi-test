"""Observability: Prometheus metrics, structured JSON logs and readiness checks.

Business metrics are derived from the audit trail (a decorator over the AuditLog port), so the
domain and use cases stay free of monitoring code. Metrics never carry personal data.
"""

import contextvars
import json
import logging
import time
import uuid
from collections.abc import Callable

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "at": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("docket")
    root.handlers[:] = [handler]
    root.setLevel(level)
    root.propagate = False


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


class Metrics:
    """One registry per application instance."""

    def __init__(self):
        self.registry = CollectorRegistry()
        r = self.registry
        self.http_requests = Counter(
            "docket_http_requests_total", "HTTP requests", ["method", "route", "status"], registry=r
        )
        self.http_latency = Histogram(
            "docket_http_request_seconds",
            "HTTP latency",
            ["route"],
            registry=r,
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
        )
        self.documents_proposed = Counter(
            "docket_documents_proposed_total", "Proposals made", ["status"], registry=r
        )
        self.review_reasons = Counter(
            "docket_review_reasons_total", "Reason codes on proposals", ["reason"], registry=r
        )
        self.documents_approved = Counter(
            "docket_documents_approved_total", "Approvals", ["action", "corrected"], registry=r
        )
        self.documents_corrected = Counter(
            "docket_documents_corrected_total", "Corrections", registry=r
        )
        self.holds_escalated = Counter(
            "docket_holds_escalated_total",
            "Suspected frauds escalated to the coordinator",
            registry=r,
        )
        self.holds_resolved = Counter(
            "docket_holds_resolved_total", "Held invoices resolved", ["outcome"], registry=r
        )
        self.import_seconds = Histogram(
            "docket_import_job_seconds",
            "Import job duration",
            registry=r,
            buckets=(0.5, 1, 2, 5, 10, 30, 60, 120),
        )
        self.queue_jobs = Gauge("docket_import_jobs", "Import jobs by state", ["state"], registry=r)

    def observe_queue(self, counts: Callable[[], dict[str, int]]) -> None:
        for state, value in counts().items():
            self.queue_jobs.labels(state=state).set(value)


class MeteredAuditLog:
    """AuditLog decorator: every audited business event also becomes a metric."""

    def __init__(self, inner, metrics: Metrics):
        self._inner, self._metrics = inner, metrics

    def record(self, actor: str, event: str, document_id: str | None = None, **details) -> None:
        self._inner.record(actor, event, document_id, **details)
        m = self._metrics
        if event == "DOCUMENT_PROPOSED":
            m.documents_proposed.labels(status=details.get("status", "UNKNOWN")).inc()
            for reason in details.get("reasons", []):
                m.review_reasons.labels(reason=reason).inc()
        elif event == "DOCUMENT_APPROVED":
            m.documents_approved.labels(
                action=details.get("action", "UNKNOWN"),
                corrected=str(bool(details.get("corrected"))).upper(),
            ).inc()
        elif event == "HOLD_ESCALATED":
            m.holds_escalated.inc()
        elif event == "DOCUMENT_CORRECTED":
            m.documents_corrected.inc()
        elif event in ("HOLD_RELEASED", "HOLD_REJECTED"):
            m.holds_resolved.labels(outcome=event.removeprefix("HOLD_")).inc()

    def list(self, document_id: str | None = None) -> list[dict]:
        return self._inner.list(document_id)


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.start
