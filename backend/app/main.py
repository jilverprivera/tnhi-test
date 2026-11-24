"""FastAPI application: Docket — assisted document filing for TAC."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.container import Container
from app.features.catalogs.api.router import router as catalogs_router
from app.features.deadlines.api.router import router as deadlines_router
from app.features.filing.api.router import outbox_router
from app.features.filing.api.router import router as filing_router
from app.features.ingestion.api.router import router as ingestion_router
from app.features.ledger.api.router import router as ledger_router
from app.shared.config import Settings, get_settings
from app.shared.infrastructure.http import AnyRole, Envelope, api_error_handler, ok


def create_app(settings: Settings | None = None) -> FastAPI:
    container = Container(settings or get_settings())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container.bootstrap()
        yield

    app = FastAPI(title="Docket API", version="0.1.0", lifespan=lifespan)
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=container.settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(StarletteHTTPException, api_error_handler)

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
        return ok("HEALTHY", {"llm_enabled": container.settings.llm_enabled})

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
    ):
        app.include_router(router)
    return app


app = create_app()
