"""The MCP tools answer from the ledger; they never write."""

import importlib

import pytest

from tests.conftest import inbox_files


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("TAC_DATA_DIR", str(tmp_path))
    from app.shared.config import get_settings

    get_settings.cache_clear()
    module = importlib.reload(importlib.import_module("app.mcp.server"))
    module.container.import_emails(inbox_files(), actor="TEST")
    yield module
    get_settings.cache_clear()


def test_what_is_due_this_week(server):
    answer = server.deadlines_this_week()
    assert answer["today"] == "2026-11-18" and answer["week"] == ["2026-11-16", "2026-11-22"]
    assert any(d["filing_number"] == "TAC-2026-ER-04792" for d in answer["due_this_week"])


def test_deadlines_in_a_range_include_unfiled_documents(server):
    found = {d["document_id"] for d in server.list_deadlines("2026-11-23", "2026-11-29")}
    assert {"11.eml__0", "12.eml__0"} <= found


def test_search_ledger_and_pending_review(server):
    assert server.search_ledger("FE-1207")[0]["filing_number"] == "TAC-2026-ER-04790"
    pending = {p["id"]: p["reasons"] for p in server.pending_review()}
    assert "INVOICE_ACCOUNT_MISMATCH" in pending["05.eml__0"]


def test_tools_are_read_only(server):
    before = server.container.ledger_repository.last_sequence()
    server.weekly_report(), server.inbox_summary(), server.search_ledger("")
    assert server.container.ledger_repository.last_sequence() == before
