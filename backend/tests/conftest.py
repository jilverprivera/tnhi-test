"""Shared fixtures. material/ is read-only: every test writes into its own temporary data dir."""

import shutil
from pathlib import Path

import pytest

from app.container import Container
from app.features.ingestion.application.split_documents import SplitDocuments
from app.features.ingestion.infrastructure.eml_reader import EmlReader
from app.features.ingestion.infrastructure.text_extractors import default_extractors
from app.shared.config import MATERIAL, Settings

INBOX = MATERIAL / "2-bandeja-de-entrada"
OCR_AVAILABLE = shutil.which("tesseract") is not None


def make_settings(data_dir: Path, **overrides) -> Settings:
    return Settings(data_dir=data_dir, llm_enabled=False, **overrides)


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
    split, reader = SplitDocuments(default_extractors()), EmlReader()
    return {p.name: split(reader.read(p.read_bytes(), p.name)) for p in sorted(INBOX.glob("*.eml"))}
