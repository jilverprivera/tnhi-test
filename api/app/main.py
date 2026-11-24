"""FastAPI application: Docket — assisted document filing for TAC."""

import logging
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.container import Container
from app.features.audit.api.router import router as audit_router
from app.features.catalogs.api.router import router as catalogs_router
from app.features.deadlines.api.router import router as deadlines_router
from app.features.filing.api.router import outbox_router
from app.features.filing.api.router import router as filing_router
from app.features.filing.api.verifications_router import router as verifications_router
from app.features.ingestion.api.router import router as ingestion_router
from app.features.ledger.api.router import router as ledger_router
from app.features.privacy.api.router import router as privacy_router
from app.features.records.api.router import router as records_router
from app.shared.config import Settings, get_settings
from app.shared.infrastructure.http import AnyRole, Envelope, api_error_handler, ok
from app.shared.infrastructure.observability import (
    Timer,
    configure_logging,
    new_request_id,
    request_id_var,
)

log = logging.getLogger("docket.http")


def create_app(settings: Settings | None = None) -> FastAPI:
    container = Container(settings or get_settings())

    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container.bootstrap()
        if container.settings.worker_enabled:
            container.import_worker.start()
        container.ledger_sync_task.start()
        yield
        container.import_worker.stop()
        container.ledger_sync_task.stop()

    app = FastAPI(title="Docket API", version="0.1.0", lifespan=lifespan)
    app.state.container = container
    if container.settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=container.settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_exception_handler(StarletteHTTPException, api_error_handler)

    @app.middleware("http")
    async def observe_requests(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or new_request_id()
        token = request_id_var.set(request_id)
        with Timer() as timer:
            response = await call_next(request)
        route = getattr(
            request.scope.get("route"), "path", "UNMATCHED"
        )  # template, never the raw id
        container.metrics.http_requests.labels(
            request.method, route, str(response.status_code)
        ).inc()
        container.metrics.http_latency.labels(route).observe(timer.seconds)
        response.headers["X-Request-ID"] = request_id
        if route not in ("/metrics", "/api/health"):
            fields = {"method": request.method, "route": route, "status": response.status_code}
            log.info("request", extra={"fields": fields | {"ms": round(timer.seconds * 1000, 1)}})
        request_id_var.reset(token)
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        """Prometheus scrape endpoint: counts and durations only, no personal data."""
        container.metrics.observe_queue(container.job_queue.counts)
        return Response(generate_latest(container.metrics.registry), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/ready", tags=["system"])
    def ready() -> JSONResponse:
        """Readiness: database, client ledger and worker. OCR missing only degrades (scans go to review)."""
        checks = {}
        try:
            with container.sessions() as s:
                s.execute(text("SELECT 1"))
            checks["database"] = "OK"
        except Exception:  # noqa: BLE001
            checks["database"] = "DOWN"
        checks["ledger_template"] = "OK" if container.settings.require("ledger_xlsx").exists() else "MISSING"
        checks["ocr"] = "OK" if shutil.which("tesseract") else "DEGRADED"
        worker_expected = container.settings.worker_enabled
        checks["import_worker"] = (
            "OK" if container.import_worker.alive or not worker_expected else "DOWN"
        )
        is_ready = all(v in ("OK", "DEGRADED") for v in checks.values())
        body = {"code": "READY" if is_ready else "NOT_READY", "data": {"checks": checks}}
        return JSONResponse(body, status_code=200 if is_ready else 503)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_, exc: RequestValidationError):
        errors = [
            {"field": ".".join(map(str, e["loc"])), "type": e["type"].upper()} for e in exc.errors()
        ]
        return JSONResponse(
            {"code": "VALIDATION_ERROR", "detail": {"errors": errors}}, status_code=422
        )

    @app.get("/api/health", tags=["system"])
    def health() -> Envelope:
        return ok("HEALTHY", {"llm_enabled": container.settings.assisted_classification_ready()})

    @app.get("/api/session", tags=["system"])
    def session(role: AnyRole) -> Envelope:
        return ok(
            "SESSION_ACTIVE", {"role": role, "today": container.settings.current_date().isoformat()}
        )

    for router in (
        ingestion_router,
        filing_router,
        outbox_router,
        ledger_router,
        deadlines_router,
        catalogs_router,
        audit_router,
        verifications_router,
        records_router,
        privacy_router,
    ):
        app.include_router(router)
    return app


app = create_app()
