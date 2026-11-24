import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import make_settings

CLERK = {"Authorization": "Bearer martha-demo"}
COORDINATOR = {"Authorization": "Bearer herrera-demo"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(make_settings(tmp_path))) as c:
        yield c


def test_responses_use_the_upper_snake_case_envelope(client):
    body = client.get("/api/health").json()
    assert body["code"] == "HEALTHY" and body["data"]["llm_enabled"] is False


def test_requires_a_token(client):
    response = client.get("/api/inbox")
    assert response.status_code == 401 and response.json()["code"] == "UNAUTHORIZED"


def test_coordinator_cannot_approve(client):
    response = client.post("/api/inbox/approve-ready", headers=COORDINATOR)
    assert response.status_code == 403 and response.json()["code"] == "FORBIDDEN"


def test_full_flow_over_http(client):
    imported = client.post("/api/ingestion/mailbox", headers=CLERK).json()
    assert imported["code"] == "EMAILS_IMPORTED" and len(imported["data"]["imported"]) == 17

    summary = client.get("/api/inbox/summary", headers=COORDINATOR).json()["data"]
    assert summary["READY"] + summary["NEEDS_REVIEW"] == 17

    held = client.get("/api/inbox/05.eml__0", headers=CLERK).json()["data"]
    assert held["decision"]["action"] == "HOLD_FOR_VERIFICATION" and held["needs_review"]
    assert "INVOICE_ACCOUNT_MISMATCH" in [r["code"] for r in held["decision"]["reasons"]]

    approved = client.post("/api/inbox/approve-ready", headers=CLERK).json()
    assert approved["code"] == "DOCUMENTS_APPROVED"

    ledger = client.get("/api/ledger", params={"q": "CD-2026-3345"}, headers=COORDINATOR).json()[
        "data"
    ]
    assert ledger[0]["department"] == "LEGAL" and ledger[0]["urgent"] is True

    report = client.get("/api/deadlines/weekly-report", headers=COORDINATOR).json()
    assert report["code"] == "WEEKLY_REPORT" and report["data"]["today"] == "2026-11-18"

    export = client.get("/api/ledger/export", headers=COORDINATOR)
    assert export.status_code == 200 and export.content[:2] == b"PK"


def test_unknown_document_returns_a_code(client):
    response = client.get("/api/inbox/nope", headers=CLERK)
    assert response.status_code == 404 and response.json()["code"] == "DOCUMENT_NOT_FOUND"


def test_validation_errors_are_upper_snake_case(client):
    response = client.post("/api/inbox/x/correct", json={"department": "NOWHERE"}, headers=CLERK)
    assert response.status_code == 422 and response.json()["code"] == "VALIDATION_ERROR"


def test_source_file_is_served(client):
    client.post("/api/ingestion/mailbox", headers=CLERK)
    response = client.get("/api/inbox/01.eml__0/source", headers=CLERK)
    assert response.status_code == 200 and response.headers["content-type"] == "application/pdf"
