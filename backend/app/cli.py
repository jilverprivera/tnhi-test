"""Command line: process the mailbox end to end (useful for demos and golden checks).

    uv run python -m app.cli process --data-dir /tmp/docket --approve-all

material/ is never written: the ledger copy lives in --data-dir.
"""

import argparse
from pathlib import Path

from app.container import Container
from app.shared.config import Settings
from app.shared.domain.models import DocumentStatus


def main() -> None:
    parser = argparse.ArgumentParser(prog="docket")
    sub = parser.add_subparsers(dest="command", required=True)
    process = sub.add_parser("process", help="import the mailbox and print the proposals")
    process.add_argument("--data-dir", type=Path, required=True)
    process.add_argument("--inbox-dir", type=Path)
    process.add_argument("--approve-all", action="store_true", help="approve every proposal as-is")
    args = parser.parse_args()

    overrides = {"data_dir": args.data_dir}
    if args.inbox_dir:
        overrides["inbox_dir"] = args.inbox_dir
    container = Container(Settings(**overrides))
    container.bootstrap()
    files = [(p.name, p.read_bytes()) for p in sorted(container.settings.inbox_dir.glob("*.eml"))]
    container.import_emails(files, actor="CLI")
    if args.approve_all:
        pending = [
            i.id
            for i in container.list_inbox()
            if i.status != DocumentStatus.APPROVED
            and not (i.decision.is_fileable and i.decision.department == "NONE")
        ]
        container.approve_documents(pending, actor="CLI")

    for item in container.list_inbox():
        d = item.decision
        print(
            f"{item.id:<12} {item.status:<13} {d.document_type:<23} {d.department:<19} {d.action:<27} "
            f"{d.due_date or ''!s:<10} {item.filing_number or '':<18} {','.join(d.reason_codes())}"
        )


if __name__ == "__main__":
    main()
