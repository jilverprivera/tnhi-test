"""HTTP conventions shared by every router.

Every response is an envelope `{"code": "UPPER_SNAKE_CASE", "data": ...}`; errors use
`{"code": "...", "detail": {...}}`. Codes are stable English identifiers the UI translates.
"""

from enum import StrEnum
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.container import Container


class Role(StrEnum):
    CLERK = "CLERK"  # Martha: imports, corrects, approves
    COORDINATOR = "COORDINATOR"  # Dra. Herrera: reads, deadlines, reports


class Envelope(BaseModel):
    code: str
    data: Any = None


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, **detail: Any):
        super().__init__(status_code=status_code, detail={"code": code, "detail": detail})


def ok(code: str, data: Any = None) -> Envelope:
    return Envelope(code=code, data=data)


async def api_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(exc.detail, status_code=exc.status_code)
    code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 422: "VALIDATION_ERROR"}.get(
        exc.status_code, "HTTP_ERROR"
    )
    return JSONResponse(
        {"code": code, "detail": {"message": str(exc.detail)}}, status_code=exc.status_code
    )


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def current_role(container: ContainerDep, authorization: Annotated[str, Header()] = "") -> Role:
    token = authorization.removeprefix("Bearer ").strip()
    if token and token == container.settings.clerk_token:
        return Role.CLERK
    if token and token == container.settings.coordinator_token:
        return Role.COORDINATOR
    raise ApiError(401, "UNAUTHORIZED")


def require_clerk(role: Annotated[Role, Depends(current_role)]) -> Role:
    if role != Role.CLERK:
        raise ApiError(403, "FORBIDDEN", required_role=Role.CLERK)
    return role


AnyRole = Annotated[Role, Depends(current_role)]
ClerkRole = Annotated[Role, Depends(require_clerk)]
