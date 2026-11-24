"""Blind set baseline (60 e-mails written without seeing the code). The rules were NOT tuned to it.

This test is a floor, not a target: it fails if a change makes the system worse on documents it has
never been fitted to. Raising the floor requires a NEW blind set (see tests/blind/README.md).
"""

import pytest

from app.container import Container
from app.evaluate import BLIND, BLIND_DIR, evaluate
from tests.conftest import OCR_AVAILABLE, make_settings

SAFETY_CRITICAL = {"HOLD_FOR_VERIFICATION", "REPLY_WITH_EXISTING_NUMBER"}


@pytest.fixture(scope="module")
def blind_report(tmp_path_factory):
    container = Container(
        make_settings(tmp_path_factory.mktemp("blind"), inbox_dir=BLIND_DIR / "emails")
    )
    container.bootstrap()
    files = [(p.name, p.read_bytes()) for p in sorted((BLIND_DIR / "emails").glob("*.eml"))]
    container.import_emails(files, actor="EVALUATION")
    return evaluate(container, (("blind", BLIND, False),))["references"]["blind"]


@pytest.mark.skipif(not OCR_AVAILABLE, reason="the blind set has 7 scanned PDFs")
def test_blind_baseline_does_not_regress(blind_report):
    assert blind_report["documents"] == 65
    assert blind_report["correct"] >= 45
    assert blind_report["wrong"] <= 6


@pytest.mark.skipif(not OCR_AVAILABLE, reason="the blind set has 7 scanned PDFs")
def test_no_fraud_hold_or_duplicate_is_ever_missed(blind_report):
    """Money-safety cases must be caught or sent to a person, never silently filed."""
    for r in blind_report["results"]:
        if r["expected"]["action"] in SAFETY_CRITICAL:
            assert r["outcome"] in ("CORRECT", "ROUTED_TO_PERSON"), r["email"]
