---
name: testing
description: Enforces backend testing for Docket with pytest — unit tests per slice (domain rules, use cases with fakes, adapters against temp files/DB, routers with TestClient), golden tests against material/4-para-medirte/esperado-parcial.csv, and regression tests for bugs. Use when adding or changing backend code or when asked about backend tests or coverage.
---

# Skill — Backend testing (pytest)

## Goal

Ship without regressions. **The backend must have tests**: every new or changed domain rule, use case, adapter and router ships with pytest tests, and the golden test stays at 100 %.

## Layout

```
backend/tests/
  conftest.py                     # shared fixtures: settings with temp dirs, in-memory DB, fakes
  shared/                         # business_calendar, identifiers, client_vocabulary
  features/<slice>/
    test_<domain_module>.py       # pure rules
    test_<use_case>.py            # use cases with fake ports
    test_<adapter>.py             # adapters against temp files / temp DB
    test_router.py                # FastAPI TestClient
  mcp/test_server.py              # each read-only tool
  golden/
    test_golden_inbox.py          # full pipeline over material/2-bandeja-de-entrada
    expected_full.csv             # the 16-row expected table (8 from the client + 8 justified)
```

## Running tests: chunked through the harness only (HARD RULE)

**NEVER** run bare `uv run pytest` over the whole tree, `pytest -n auto` / xdist, or `--looponfail`: it saturates the machine's RAM. Use the harness:

```bash
./scripts/harness-verify.sh --backend                                   # ruff on changed files + pytest batches for changed slices
./scripts/harness-verify.sh backend/tests/features/filing/test_invoice_rules.py   # explicit file(s)
./scripts/harness-verify.sh --backend --full                            # whole suite, chunked: only when the user asks
```

The harness runs `uv run pytest -q -p no:cacheprovider` on 3 files per batch, one batch at a time, under the `pytest` lock, with a RAM guard. Keep test files mapped to the layout below so `--changed` finds them (`backend/app/features/<slice>/**` -> `backend/tests/features/<slice>/`). Report which batches ran.

## Policy (HARD RULE)

| Artifact | Test |
|---|---|
| Domain rule / calculation | Unit, table-driven (`pytest.mark.parametrize`) |
| Use case | Unit with fake ports (plain classes implementing the Protocol) |
| Adapter (eml, pdf/ocr, csv, SQLAlchemy, openpyxl) | Against fixtures or temp copies |
| Router | `TestClient`: status codes, `snake_case` keys, `UPPER_SNAKE_CASE` codes |
| MCP tool | Call the tool function, assert read-only result |
| Bug fix | Regression test that fails before the fix |

## Must-have cases

- Business calendar: 10-nov -> 2-dic (15 days, 16-nov holiday), 13-nov + 5 -> 23-nov, 17-nov + 15 -> 9-dic (8-dic holiday); count starts the business day after reception.
- NIT verification digit valid/invalid.
- Each invoice rule: unknown supplier, inactive supplier, duplicate, account/domain mismatch -> `HOLD_FOR_VERIFICATION`, with/without purchase order.
- Travel requests: missing form/approval -> `RETURN_TO_SENDER`; < 5 business days -> late flag.
- Petitions: 15/10/30 days; tutela mention -> urgent. Oversight notices: deadline from the text; unreadable -> `NEEDS_REVIEW`.
- Excel: header/formats/existing rows unchanged, new numbers 04818... consecutive.

## Golden test

- Runs the whole pipeline with `today=2026-11-18` on a temp copy of the client data.
- Must match 100 % of `material/4-para-medirte/esperado-parcial.csv` and the full expected table for type, department, action, due date and filing number.
- Never edit expected files to make the test pass without a written justification in the feature docs.

## Rules

- Test names in English, behavior-focused: `test_invoice_with_changed_account_is_held_for_verification`.
- Deterministic: inject `today`; no network; no reliance on test order.
- Never write to `material/`: copy fixtures to `tmp_path`.
- Mock only at ports; keep domain logic real.
- Minimum per use case: happy path + one failure path; prefer all reason codes it can emit.

## Checklist

| # | Check |
|---|---|
| 1 | New/changed rule or use case has tests? |
| 2 | Adapter tested against temp files/DB? |
| 3 | Router test checks codes and key casing? |
| 4 | Golden test 100 %? |
| 5 | Regression test for bug fixes? |
| 6 | `./scripts/harness-verify.sh --backend` green (never a bare full pytest run)? |
| 7 | "How it is tested" section updated in the feature docs (en + es)? |
