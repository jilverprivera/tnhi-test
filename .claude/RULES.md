# Docket — Hard rules

Complements `CLAUDE.md`. If a skill and this file disagree, this file wins.

## Process

- Multi-agent roles: `.claude/agents/leader.md`, `implementer.md`, `reviewer.md`.
- Notes on disk: `progress/<topic>/` (`plan.md`, `explore_*.md`, `impl_*.md`, `review_*.md`), team log `progress/history.md`. See `.claude/skills/harness/SKILL.md`.
- Final checklist: `.claude/CHECKPOINTS.md`.
- **Git:** the human owns branches and commits. Never `git commit` / `git push` / `git stash`, never create or switch branches, unless the user asks.
- Another agent may be editing the tree at the same time: edit only the paths you were given, re-read a file right before editing it, never revert lines you did not write.

| Pillar | Location |
|---|---|
| The repository is the system | `CLAUDE.md`, `.claude/CHECKPOINTS.md`, `progress/`, `docs/` |
| Multi-agent orchestration | `.claude/agents/` |
| Conventions | `.claude/skills/*/SKILL.md` |
| Supervision | `reviewer` agent, `.claude/CHECKPOINTS.md`, this file |

## How to use skills

1. Identify the scope: `backend`, `frontend`, or `cross-stack`.
2. Open only the skills listed for that scope in `CLAUDE.md` section 8.
3. Before closing, walk `.claude/CHECKPOINTS.md`.

## Verification — chunked tests only (HARD RULE)

**NEVER run a test suite in one go or with unbounded parallelism** — frontend (bare `pnpm test`, `npx jest`, `jest --watch`, high `--maxWorkers`) or backend (bare `uv run pytest` over the whole tree, `pytest -n auto`/xdist, `--looponfail`): it saturates the machine's RAM. Run tests only through `./scripts/harness-verify.sh`: staged by changed files, a few test files per batch, one batch at a time under a per-runner lock (`pytest`, `jest`, `playwright` in `${TMPDIR}/docket-locks/`), with a RAM guard before each batch. The full suite (`--full`) only when the user explicitly asks, and still through the harness.

| Scope | Commands |
|---|---|
| backend | `./scripts/harness-verify.sh --backend` (ruff on changed files + pytest batches) |
| frontend | `./scripts/harness-verify.sh --frontend` (pnpm lint + jest `--maxWorkers=1` batches), `cd web && pnpm build` |
| e2e | `./scripts/harness-verify.sh --e2e` (Playwright `--workers=1`) |
| cross-stack | `./scripts/harness-verify.sh --all` |

**Both stacks must have tests:** every backend use case and domain rule ships with pytest tests (unit per slice + golden tests vs `material/4-para-medirte/esperado-parcial.csv`); frontend with Jest + React Testing Library; E2E with Playwright.

Never invent scripts that are not in `scripts/`, `pyproject.toml` or `package.json`.

## Domain hard rules

- `material/` is read-only. Tests and the CLI work on copies.
- The Excel ledger keeps its 12 columns and formats; Docket appends its rows and, through the two-way sync (`SyncLedger`), writes only the cells it changed — people's edits are merged, never overwritten, and an open file is never written.
- Filing numbers `TAC-2026-ER-#####` are assigned on approval (`last_sequence() + 1` from the DB ledger), serialized by an in-process lock plus a DB unique constraint, and never reused. Multi-process deployments would need `SELECT ... FOR UPDATE` or a DB sequence (known gap); there is no voiding flow yet.
- A document with any blocking reason is `NEEDS_REVIEW` and is never forwarded automatically.
- Invoice fraud signals (bank account or sender domain differs from the supplier master) always end in `HOLD_FOR_VERIFICATION`.
- Deadlines are Colombian business days, counted from the business day after reception, with the `holidays` CO calendar plus `TAC_EXTRA_HOLIDAYS`.
- The LLM adapter is off by default, receives masked personal data, and never decides alone.
- The MCP server is read-only: no tool may mutate state.

## Mandatory bilingual feature documentation

Every feature the system ships must come with Markdown documentation of how that part of the app works, in **both English and Spanish**, under the repository-root `docs/` folder:

- `docs/en/features/<feature-slug>.md` and `docs/es/features/<feature-slug>.md`: same slug (the api/web feature folder name: `inbox`, `document-review`, `ledger`, `deadlines`, `settings`, `ingestion`, `classification`, `filing`, `catalogs`, `audit`, `records`, `privacy`, `compliance`, plus `mcp`, `pwa`, `observability` and `evaluation`), same section structure.
- Both listed in `docs/en/README.md` and `docs/es/README.md`.
- Sections: purpose, who uses it (clerk / coordinator / AI assistant via MCP), how it works (flow), business rules, API endpoints or screens, reason/status codes it emits (`UPPER_SNAKE_CASE` with English and Spanish meaning), limitations, how it is tested.
- A feature without both docs updated is **not done**; the reviewer rejects it.
- `docs/en/` and `docs/es/` also hold the interview deliverables (architecture, features, solution, domain model, quality attributes).

Template: `.claude/skills/documentation-web/SKILL.md`.

## Mandatory audit events (backend)

Every mutating or decision action (import, proposal, approve, batch approve, correct, discard, supplier master replacement) records an audit event (`AuditRow`: autoincrement `id`, `at` timestamp, `actor`, `event` code in `UPPER_SNAKE_CASE`, `document_id`, JSON `details` such as the changed fields on a correction). Known gaps: rejected approvals are not audited and discard reasons are not masked. Details: `.claude/skills/audit-logging/SKILL.md`.

## Language

All code, identifiers, comments, test names and API values in English. Spanish only in frontend i18n labels, the client's Excel ledger values, and `docs/es/`.
