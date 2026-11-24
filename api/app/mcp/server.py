"""Read-only MCP server: exposes the filing ledger to an AI assistant.

The coordinator can ask her assistant "what is due this week?". Tools only read; nothing is
filed, corrected or sent through MCP.

    uv run python -m app.mcp.server            # stdio (Claude Desktop / Claude Code)
    (MCP Python SDK 2.x: FastMCP is now MCPServer)
    uv run python -m app.mcp.server --http     # streamable HTTP on :8001
"""

import sys
from datetime import date, timedelta

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from app.container import Container
from app.features.deadlines.domain.deadline import week_bounds
from app.features.ledger.application.use_cases import LedgerQuery
from app.shared.config import get_settings
from app.shared.domain.models import DocumentStatus

container = Container(get_settings())
container.bootstrap()

mcp = MCPServer(
    "docket",
    version="0.1.0",
    instructions=(
        "Read-only access to Terminales Andinas de Carga's filing ledger (libro de radicación). "
        "Use it to answer questions about filed documents, legal deadlines (petitions, oversight "
        "notices, complaints) and documents waiting for human review. Dates are ISO (YYYY-MM-DD); "
        "codes are UPPER_SNAKE_CASE English identifiers."
    ),
)


READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)


def _today() -> date:
    return container.settings.current_date()


@mcp.tool(annotations=READ_ONLY)
def deadlines_this_week() -> dict:
    """What is due this week (Monday to Sunday), plus anything overdue. Urgent items first."""
    report = container.weekly_report(_today())
    return {
        "today": report.today.isoformat(),
        "week": [report.week_start.isoformat(), report.week_end.isoformat()],
        "overdue": [d.model_dump(mode="json") for d in report.overdue],
        "due_this_week": [d.model_dump(mode="json") for d in report.this_week],
    }


@mcp.tool(annotations=READ_ONLY)
def weekly_report() -> dict:
    """The coordinator's Friday report: overdue, this week, next week and not-yet-filed counts."""
    return container.weekly_report(_today()).model_dump(mode="json")


@mcp.tool(annotations=READ_ONLY)
def list_deadlines(start: str | None = None, end: str | None = None) -> list[dict]:
    """Open deadlines between two ISO dates (defaults: today to 30 days ahead)."""
    start_date = date.fromisoformat(start) if start else _today()
    end_date = date.fromisoformat(end) if end else _today() + timedelta(days=30)
    return [
        d.model_dump(mode="json") for d in container.list_deadlines(_today(), start_date, end_date)
    ]


@mcp.tool(annotations=READ_ONLY)
def search_ledger(
    query: str, department: str = "", document_type: str = "", limit: int = 20
) -> list[dict]:
    """Search the ledger by filing number, sender, NIT, subject or document number.

    department: ACCOUNTS_PAYABLE, PROCUREMENT, HUMAN_RESOURCES, LEGAL, CUSTOMER_SERVICE, ADMIN_COORDINATION.
    document_type: INVOICE, TRAVEL_EXPENSE_REQUEST, PETITION, OVERSIGHT_NOTICE, COMPLAINT, QUOTATION.
    """
    entries = container.list_ledger(
        LedgerQuery(text=query, department=department, document_type=document_type)
    )
    return [e.model_dump(mode="json") for e in entries[: max(1, min(limit, 100))]]


@mcp.tool(annotations=READ_ONLY)
def pending_review() -> list[dict]:
    """Documents the system was not sure about, with the reason codes a person must resolve."""
    return [
        {
            "id": i.id,
            "received_at": i.received_at.isoformat(),
            "sender": i.proposal.document.sender,
            "subject": i.proposal.document.email_subject,
            "document_type": i.decision.document_type,
            "reasons": [r.code for r in i.decision.reasons if r.blocking],
        }
        for i in container.list_inbox(DocumentStatus.NEEDS_REVIEW)
    ]


@mcp.tool(annotations=READ_ONLY)
def held_invoices() -> list[dict]:
    """Invoices held for possible fraud and where each stands.

    verification_state: PENDING_CLERK_APPROVAL (still in the clerk's inbox), AWAITING_VERIFICATION
    (the coordinator must call the supplier), RELEASED or REJECTED.
    """
    return [
        {
            "id": item.id,
            "filing_number": item.filing_number,
            "supplier": item.proposal.data.sender_name or item.proposal.document.sender_name,
            "invoice": item.proposal.data.document_number,
            "total_amount": item.proposal.data.total_amount,
            "sender": item.proposal.document.sender,
            "verification_state": state,
            "reasons": [r.code for r in item.decision.reasons if r.code != "REVIEWED_BY_HUMAN"],
        }
        for item, state in container.list_held_invoices()
    ]


@mcp.tool(annotations=READ_ONLY)
def inbox_summary() -> dict:
    """How many documents are READY, NEEDS_REVIEW, APPROVED or DISCARDED."""
    return container.inbox_summary()


@mcp.resource("docket://week")
def current_week() -> str:
    """The current week's bounds, as the server sees them."""
    monday, sunday = week_bounds(_today())
    return f"{monday.isoformat()}..{sunday.isoformat()}"


if __name__ == "__main__":
    if "--http" in sys.argv:
        # The MCP server has no auth of its own: bind it to localhost (see docs/en/features/mcp.md)
        settings = container.settings
        mcp.run(
            transport="streamable-http",
            host=settings.require("mcp_host"),
            port=settings.require("mcp_port"),
        )
    else:
        mcp.run()
