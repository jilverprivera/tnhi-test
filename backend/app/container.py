"""Composition root: wires adapters into use cases. The only place that knows every slice."""

from dataclasses import dataclass
from functools import cached_property

from app.features.audit.application.list_audit import ListAudit
from app.features.audit.infrastructure.sql_audit_log import SqlAuditLog
from app.features.catalogs.infrastructure.csv_catalogs import CsvCatalogs
from app.features.classification.application.classify_document import ClassifyDocument
from app.features.classification.infrastructure.disabled_classifier import DisabledClassifier
from app.features.deadlines.application.list_deadlines import BuildWeeklyReport, ListDeadlines
from app.features.filing.application.approve_documents import (
    ApproveDocuments,
    ApproveReadyDocuments,
)
from app.features.filing.application.correct_document import CorrectDocument, DiscardDocument
from app.features.filing.application.propose_filing import ProposeFiling
from app.features.filing.application.queries import (
    GetInboxItem,
    InboxSummary,
    ListInbox,
    ListOutbox,
)
from app.features.filing.infrastructure.sql_repositories import (
    SqlInboxRepository,
    SqlOutbox,
)
from app.features.ingestion.application.import_emails import ImportEmails
from app.features.ingestion.application.split_documents import SplitDocuments
from app.features.ingestion.infrastructure.eml_reader import EmlReader
from app.features.ingestion.infrastructure.text_extractors import default_extractors
from app.features.ledger.application.use_cases import (
    ExportLedger,
    FindLedgerDuplicates,
    ListLedger,
    SeedLedger,
)
from app.features.ledger.infrastructure.excel_ledger import ExcelLedgerWorkbook
from app.features.ledger.infrastructure.sql_ledger import SqlLedgerRepository
from app.shared.config import Settings
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.infrastructure.db import build_engine, build_session_factory


@dataclass
class Container:
    settings: Settings

    # --- infrastructure ---------------------------------------------------------------
    @cached_property
    def sessions(self):
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
        return build_session_factory(build_engine(self.settings.db_url()))

    @cached_property
    def calendar(self) -> BusinessCalendar:
        return BusinessCalendar(self.settings.extra_holidays)

    @cached_property
    def catalogs(self) -> CsvCatalogs:
        working_master = self.settings.data_dir / "maestro-proveedores.csv"
        if not working_master.exists():
            self.settings.data_dir.mkdir(parents=True, exist_ok=True)
            working_master.write_bytes(self.settings.suppliers_csv.read_bytes())
        return CsvCatalogs(working_master, self.settings.departments_csv)

    @cached_property
    def ledger_repository(self) -> SqlLedgerRepository:
        return SqlLedgerRepository(self.sessions)

    @cached_property
    def workbook(self) -> ExcelLedgerWorkbook:
        return ExcelLedgerWorkbook(
            self.settings.ledger_xlsx, self.settings.data_dir / "libro-radicacion-2026.xlsx"
        )

    @cached_property
    def inbox_repository(self) -> SqlInboxRepository:
        return SqlInboxRepository(self.sessions)

    @cached_property
    def outbox(self) -> SqlOutbox:
        return SqlOutbox(self.sessions)

    @cached_property
    def audit(self) -> SqlAuditLog:
        return SqlAuditLog(self.sessions)

    @cached_property
    def assisted_classifier(self):
        if self.settings.llm_enabled and self.settings.anthropic_api_key:
            from app.features.classification.infrastructure.claude_classifier import (
                ClaudeClassifier,
            )

            return ClaudeClassifier(self.settings.anthropic_api_key, self.settings.llm_model)
        return DisabledClassifier()

    # --- use cases --------------------------------------------------------------------
    @cached_property
    def seed_ledger(self) -> SeedLedger:
        return SeedLedger(self.ledger_repository, self.workbook, self.settings.filing_prefix)

    @cached_property
    def propose_filing(self) -> ProposeFiling:
        classify = ClassifyDocument(
            self.assisted_classifier,
            self.settings.company_nit,
            self.settings.min_classification_margin,
        )
        return ProposeFiling(
            classify,
            self.catalogs,
            self.ledger_repository,
            self.calendar,
            self.settings.min_ocr_confidence,
        )

    @cached_property
    def import_emails(self) -> ImportEmails:
        return ImportEmails(
            EmlReader(),
            SplitDocuments(default_extractors()),
            self.propose_filing,
            self.inbox_repository,
            self.audit,
        )

    @cached_property
    def approve_documents(self) -> ApproveDocuments:
        return ApproveDocuments(
            self.inbox_repository,
            self.ledger_repository,
            self.workbook,
            self.outbox,
            self.audit,
            self.catalogs,
            self.settings.filing_prefix,
        )

    @cached_property
    def approve_ready(self) -> ApproveReadyDocuments:
        return ApproveReadyDocuments(self.inbox_repository, self.approve_documents)

    @cached_property
    def correct_document(self) -> CorrectDocument:
        return CorrectDocument(self.inbox_repository, self.audit)

    @cached_property
    def discard_document(self) -> DiscardDocument:
        return DiscardDocument(self.inbox_repository, self.audit)

    @cached_property
    def list_inbox(self) -> ListInbox:
        return ListInbox(self.inbox_repository)

    @cached_property
    def inbox_summary(self) -> InboxSummary:
        return InboxSummary(self.inbox_repository)

    @cached_property
    def get_inbox_item(self) -> GetInboxItem:
        return GetInboxItem(self.inbox_repository)

    @cached_property
    def list_outbox(self) -> ListOutbox:
        return ListOutbox(self.outbox)

    @cached_property
    def list_audit(self) -> ListAudit:
        return ListAudit(self.audit)

    @cached_property
    def list_ledger(self) -> ListLedger:
        return ListLedger(self.ledger_repository)

    @cached_property
    def export_ledger(self) -> ExportLedger:
        return ExportLedger(self.ledger_repository, self.workbook)

    @cached_property
    def find_ledger_duplicates(self) -> FindLedgerDuplicates:
        return FindLedgerDuplicates(self.ledger_repository)

    @cached_property
    def list_deadlines(self) -> ListDeadlines:
        return ListDeadlines(self.ledger_repository, self.inbox_repository, self.calendar)

    @cached_property
    def weekly_report(self) -> BuildWeeklyReport:
        return BuildWeeklyReport(self.list_deadlines)

    def bootstrap(self) -> None:
        self.seed_ledger()
