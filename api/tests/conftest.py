"""Shared fixtures. material/ is read-only: every test writes into its own temporary data dir."""

import shutil
from datetime import date
from pathlib import Path

import pytest

from app.container import Container
from app.features.ingestion.application.split_documents import SplitDocuments
from app.features.ingestion.infrastructure.eml_reader import EmlReader
from app.features.ingestion.infrastructure.text_extractors import default_extractors
from app.shared.config import MATERIAL, Settings

INBOX = MATERIAL / "2-bandeja-de-entrada"
OCR_AVAILABLE = shutil.which("tesseract") is not None


CLIENT_DATA = MATERIAL / "3-datos-del-cliente"


def make_settings(data_dir: Path, **overrides) -> Settings:
    """Every value explicit and api/.env ignored: tests never depend on the developer's machine."""
    values = {
        "data_dir": data_dir,
        "database_url": f"sqlite:///{data_dir / 'tac.db'}",
        "inbox_dir": INBOX,
        "suppliers_csv": CLIENT_DATA / "maestro-proveedores.csv",
        "departments_csv": CLIENT_DATA / "dependencias.csv",
        "ledger_xlsx": CLIENT_DATA / "libro-radicacion-2026.xlsx",
        "today": date(2026, 11, 18),
        "company_nit": "900.100.200-3",
        "filing_prefix": "TAC-2026-ER-",
        "ocr_language": "spa",
        "min_ocr_confidence": 70.0,
        "min_classification_margin": 2.0,
        "llm_enabled": False,
        "worker_enabled": True,
        "worker_poll_seconds": 0.5,
        "ledger_sync_seconds": 0,  # deterministic: syncs happen on demand
        "clerk_token": "martha-demo",
        "coordinator_token": "herrera-demo",
        "cors_origins": ["http://localhost:3000"],
    }
    return Settings(_env_file=None, **(values | overrides))


def inbox_files() -> list[tuple[str, bytes]]:
    return [(p.name, p.read_bytes()) for p in sorted(INBOX.glob("*.eml"))]


@pytest.fixture
def container(tmp_path: Path) -> Container:
    c = Container(make_settings(tmp_path))
    c.bootstrap()
    return c


@pytest.fixture(scope="session")
def imported_container(tmp_path_factory) -> Container:
    """The whole mailbox imported once (proposals only, nothing approved)."""
    c = Container(make_settings(tmp_path_factory.mktemp("imported")))
    c.bootstrap()
    c.import_emails(inbox_files(), actor="TEST")
    return c


@pytest.fixture(scope="session")
def documents_by_email():
    split, reader = SplitDocuments(default_extractors("spa")), EmlReader()
    return {p.name: split(reader.read(p.read_bytes(), p.name)) for p in sorted(INBOX.glob("*.eml"))}
