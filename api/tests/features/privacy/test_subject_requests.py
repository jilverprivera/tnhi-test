"""Habeas data (Ley 1581 de 2012): find a person's data, answer on time, leave no trace of it."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.features.privacy.application.subject_requests import IdentifierTooShortError, RequestKind
from app.main import create_app
from tests.conftest import inbox_files, make_settings


@pytest.fixture
def loaded(container):
    container.import_emails(inbox_files(), actor="TEST")
    container.approve_documents(["07.eml__0"], actor="CLERK")
    return container


def test_finds_an_employee_by_national_id(loaded):
    report = loaded.find_data_subject(
        "80.123.456", RequestKind.INQUIRY, date(2026, 11, 18), actor="COORDINATOR"
    )
    places = {(m.where, m.reference) for m in report.matches}
    assert ("INBOX", "07.eml__0") in places and any(m.where == "LEDGER" for m in report.matches)
    assert report.response_due == date(2026, 12, 2)  # 10 business days (Ley 1581 art. 14)


def test_finds_a_citizen_by_email_and_claims_have_15_days(loaded):
    report = loaded.find_data_subject(
        "andrea.villamizar@diariosabana.example", RequestKind.CLAIM, date(2026, 11, 18), "C"
    )
    assert [m.reference for m in report.matches] == ["12.eml__0"]
    assert report.response_due == date(2026, 12, 10)  # 15 business days, 8-Dec holiday (art. 15)


def test_the_audit_never_stores_the_identifier(loaded):
    loaded.find_data_subject(
        "80.123.456", RequestKind.INQUIRY, date(2026, 11, 18), actor="COORDINATOR"
    )
    event = next(e for e in loaded.list_audit() if e["event"] == "PRIVACY_SUBJECT_LOOKUP")
    assert event["details"]["identifier"] == "***.456" and "80.123.456" not in str(event)


def test_too_short_identifiers_are_rejected(loaded):
    with pytest.raises(IdentifierTooShortError):
        loaded.find_data_subject("123", RequestKind.INQUIRY, date(2026, 11, 18), actor="C")


def test_discard_reasons_are_masked_in_the_audit(loaded):
    loaded.discard_document(
        "15.eml__0", "Publicidad; escribió desde novedades@contablenube.example", actor="CLERK"
    )
    event = next(e for e in loaded.list_audit("15.eml__0") if e["event"] == "DOCUMENT_DISCARDED")
    assert "@" not in event["details"]["reason"] and "[EMAIL]" in event["details"]["reason"]


def test_only_the_coordinator_runs_subject_requests_and_ids_travel_in_the_body(tmp_path):
    with TestClient(create_app(make_settings(tmp_path))) as client:
        clerk = {"Authorization": "Bearer martha-demo"}
        coordinator = {"Authorization": "Bearer herrera-demo"}
        assert (
            client.get("/api/privacy/inventory", headers=clerk).json()["code"]
            == "PRIVACY_INVENTORY"
        )
        body = {"identifier": "80.123.456", "kind": "INQUIRY"}
        assert (
            client.post("/api/privacy/subject-requests", json=body, headers=clerk).status_code
            == 403
        )
        ok = client.post("/api/privacy/subject-requests", json=body, headers=coordinator).json()
        assert ok["code"] == "SUBJECT_REPORT" and ok["data"]["identifier_masked"] == "***.456"
