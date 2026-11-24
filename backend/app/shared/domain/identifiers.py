"""Identifier helpers: NIT, bank accounts, document numbers and e-mail domains."""

import re


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_nit(nit: str) -> str:
    """NIT without dots or dash, including the check digit."""
    return digits_only(nit)


def is_valid_nit(nit: str) -> bool:
    """Validate a Colombian NIT check digit (DIAN modulo-11 algorithm)."""
    match = re.fullmatch(r"\s*([\d.]+)-(\d)\s*", nit or "")
    if not match:
        return False
    base = digits_only(match.group(1))
    weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    remainder = sum(int(c) * weights[i] for i, c in enumerate(reversed(base))) % 11
    return int(match.group(2)) == (remainder if remainder < 2 else 11 - remainder)


def normalize_account(account: str) -> str:
    return digits_only(account)


def normalize_document_number(number: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (number or "").upper())


def email_domain(address: str) -> str:
    return address.rsplit("@", 1)[-1].strip().lower() if "@" in (address or "") else ""
