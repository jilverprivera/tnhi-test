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
    ]["items"]
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


def test_audit_endpoint_and_master_reload_are_audited(client):
    client.put(
        "/api/catalogs/suppliers",
        files={"file": ("m.csv", b"nit,razon_social\n1,x\n", "text/csv")},
        headers=CLERK,
    )
    events = client.get("/api/audit", headers=COORDINATOR).json()
    assert events["code"] == "AUDIT_LISTED"
    assert any(e["event"] == "SUPPLIER_MASTER_REJECTED" for e in events["data"])


def test_only_the_coordinator_resolves_held_invoices(client):
    client.post("/api/ingestion/mailbox", headers=CLERK)
    client.post("/api/inbox/05.eml__0/escalate", headers=CLERK)
    listed = client.get("/api/verifications", headers=COORDINATOR).json()
    assert listed["data"][0]["verification_state"] == "AWAITING_VERIFICATION"
    assert (
        listed["data"][0]["master_supplier"]["billing_email"]
        == "facturacion@aseointegralbogota.example"
    )
    as_clerk = client.post(
        "/api/verifications/05.eml__0/release", json={"note": "verificado"}, headers=CLERK
    )
    assert as_clerk.status_code == 403 and as_clerk.json()["code"] == "FORBIDDEN"
    short = client.post(
        "/api/verifications/05.eml__0/release", json={"note": "ok"}, headers=COORDINATOR
    )
    assert short.json()["code"] == "VERIFICATION_NOTE_REQUIRED"
    done = client.post(
        "/api/verifications/05.eml__0/release",
        json={"note": "Llamé al proveedor"},
        headers=COORDINATOR,
    )
    assert (
        done.json()["code"] == "HOLD_RELEASED"
        and done.json()["data"]["verification_state"] == "RELEASED"
    )
    again = client.post(
        "/api/verifications/05.eml__0/reject", json={"note": "fraude"}, headers=COORDINATOR
    )
    assert again.status_code == 409 and again.json()["code"] == "HOLD_NOT_PENDING"


def test_inbox_and_ledger_are_paginated(client):
    client.post("/api/ingestion/mailbox", headers=CLERK)
    first = client.get("/api/inbox", params={"limit": 5}, headers=CLERK).json()["data"]
    assert (first["total"], first["limit"], first["offset"], len(first["items"])) == (17, 5, 0, 5)
    last = client.get("/api/inbox", params={"limit": 5, "offset": 15}, headers=CLERK).json()["data"]
    assert len(last["items"]) == 2
    assert {i["id"] for i in first["items"]}.isdisjoint(i["id"] for i in last["items"])
    pending = client.get(
        "/api/inbox",
        params=[("status", "NEEDS_REVIEW"), ("status", "READY"), ("limit", 100)],
        headers=CLERK,
    ).json()["data"]
    assert pending["total"] == 17
    ledger = client.get("/api/ledger", params={"limit": 10, "offset": 20}, headers=CLERK).json()[
        "data"
    ]
    assert (ledger["total"], len(ledger["items"])) == (28, 8)
    huge = client.get("/api/ledger", params={"limit": 10_000}, headers=CLERK).json()["data"]
    assert huge["limit"] == 200  # clamped


def test_approve_rejects_holds_and_escalate_alerts_the_coordinator(client):
    client.post("/api/ingestion/mailbox", headers=CLERK)
    rejected = client.post("/api/inbox/approve", json={"ids": ["05.eml__0"]}, headers=CLERK)
    assert rejected.status_code == 409 and rejected.json()["code"] == "HOLD_REQUIRES_ESCALATION"
    escalated = client.post("/api/inbox/05.eml__0/escalate", headers=CLERK).json()
    assert escalated["code"] == "HOLD_ESCALATED" and escalated["data"]["filing_number"]
    not_hold = client.post("/api/inbox/01.eml__0/escalate", headers=CLERK)
    assert not_hold.status_code == 409 and not_hold.json()["code"] == "NOT_A_HOLD"
