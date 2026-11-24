"""Filing numbers: TAC-2026-ER-#####, one consecutive per filed document."""

import re

DIGITS = 5


def parse_sequence(filing_number: str, prefix: str) -> int | None:
    match = re.fullmatch(re.escape(prefix) + r"(\d+)", filing_number.strip())
    return int(match.group(1)) if match else None


def format_filing_number(prefix: str, sequence: int) -> str:
    return f"{prefix}{sequence:0{DIGITS}d}"
