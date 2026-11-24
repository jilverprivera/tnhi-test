from app.shared.domain.identifiers import (
    email_domain,
    is_valid_nit,
    normalize_account,
    normalize_document_number,
    normalize_nit,
)


def test_normalize_nit_keeps_only_digits():
    assert normalize_nit("901.234.567-1") == "9012345671"


def test_nit_check_digit_dian_algorithm():
    assert is_valid_nit("800.197.268-4")  # DIAN's own NIT
    assert not is_valid_nit("800.197.268-5")
    assert not is_valid_nit("not a nit")


def test_account_and_document_number_normalization():
    assert normalize_account("245-000123-45") == normalize_account("24500012345")
    assert normalize_document_number("fe-1207") == normalize_document_number("FE 1207") == "FE1207"


def test_email_domain():
    assert email_domain("Facturacion@AseoIntegral-Bogota.example") == "aseointegral-bogota.example"
    assert email_domain("no-at-sign") == ""
