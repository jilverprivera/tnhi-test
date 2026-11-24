# Docket — Checkpoints before "done"

The implementer self-checks; the reviewer verifies and records each item in `review_<topic>.md`.

## C1 — Scope and architecture
- [ ] Change stays inside the assigned paths and one primary scope.
- [ ] Backend: dependency rule respected (`domain <- application <- infrastructure/api`); no slice imports another slice's infrastructure; wiring only in `container.py`.
- [ ] Frontend: no feature-to-feature import; atomic layer order respected; one component per file; routes in `app/` stay thin.

## C2 — Conventions
- [ ] All code, identifiers, comments and test names in English.
- [ ] API values and error codes `UPPER_SNAKE_CASE`; JSON keys `snake_case`.
- [ ] Spanish only in `web/src/shared/i18n/` and Excel ledger values (via `client_vocabulary.py`).
- [ ] No secrets in code; config through `app/shared/config.py` (`TAC_*`).
- [ ] Light and dark theme supported with tokens; layout works at 375, 768 and 1440 px.

## C3 — Domain safety
- [ ] `material/` untouched.
- [ ] Excel ledger format preserved (columns, styles, existing rows).
- [ ] Filing numbers assigned only on approval and never reused.
- [ ] Anything uncertain goes to `NEEDS_REVIEW` with a visible reason code.
- [ ] Mutating actions record an audit event.

## C4 — Tests
- [ ] Backend use cases and domain rules have pytest tests; frontend behavior has Jest + RTL tests; user flows have Playwright specs.
- [ ] New or changed behavior has tests (happy, failure, edge).
- [ ] Bug fixes have a regression test.
- [ ] Golden test still at 100 % against `material/4-para-medirte/esperado-parcial.csv`.

## C5 — Verification evidence (chunked, never one big run)
- [ ] Tests ran only through `./scripts/harness-verify.sh` (no bare `uv run pytest` over the tree, no bare `pnpm test`, no xdist/`--watch`/high `--maxWorkers`).
- [ ] Backend: `./scripts/harness-verify.sh --backend` green (ruff + pytest batches).
- [ ] Frontend: `./scripts/harness-verify.sh --frontend` green and `cd web && pnpm build` green.
- [ ] E2E: `./scripts/harness-verify.sh --e2e` green for changed specs (Playwright `--workers=1`).
- [ ] `--full` only if the user asked for it.
- [ ] Batches run and the summary output recorded in `impl_<topic>.md`.

## C6 — Bilingual feature documentation (a feature is NOT done without it)
- [ ] `docs/en/features/<feature-slug>.md` and `docs/es/features/<feature-slug>.md` exist, same slug as the feature folder, same section structure.
- [ ] Sections: purpose, users (clerk / coordinator / AI assistant via MCP), flow, business rules, endpoints or screens, codes emitted (English + Spanish meaning), limitations, how it is tested.
- [ ] Docs reflect this change and are listed in `docs/en/README.md` and `docs/es/README.md`.
