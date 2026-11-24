import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import make_settings

CLERK = {"Authorization": "Bearer martha-demo"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(make_settings(tmp_path, worker_poll_seconds=0.05))) as c:
        yield c


def _wait_for(client, job_id, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/ingestion/jobs/{job_id}", headers=CLERK).json()["data"]
        if job["state"] in ("DONE", "FAILED"):
            return job
        time.sleep(0.1)
    raise AssertionError("job did not finish")


def test_queued_import_is_processed_by_the_worker(client):
    queued = client.post("/api/ingestion/jobs/mailbox", headers=CLERK)
    assert queued.status_code == 202 and queued.json()["code"] == "IMPORT_QUEUED"
    job = _wait_for(client, queued.json()["data"]["id"])
    assert job["state"] == "DONE" and len(job["result"]["imported"]) == 17
    listed = client.get("/api/ingestion/jobs", headers=CLERK).json()["data"]
    assert listed["counts"]["DONE"] == 1


def test_metrics_expose_business_counts_without_personal_data(client):
    _wait_for(
        client, client.post("/api/ingestion/jobs/mailbox", headers=CLERK).json()["data"]["id"]
    )
    client.post("/api/inbox/approve-ready", headers=CLERK)
    body = client.get("/metrics").text
    assert 'docket_documents_proposed_total{status="READY"}' in body
    assert 'docket_review_reasons_total{reason="INVOICE_ACCOUNT_MISMATCH"}' in body
    assert (
        "docket_documents_approved_total" in body and "docket_import_job_seconds_count 1.0" in body
    )
    for secret in ("901.112.233-4", "aseointegral", "@", "martha-demo"):
        assert secret not in body


def test_request_id_and_readiness(client):
    response = client.get("/api/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"
    ready = client.get("/api/ready")
    assert ready.status_code == 200 and ready.json()["code"] == "READY"
    assert ready.json()["data"]["checks"]["database"] == "OK"
    assert ready.json()["data"]["checks"]["import_worker"] == "OK"
