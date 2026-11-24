---
name: harness
description: Lean multi-agent workflow for Docket — leader/implementer/reviewer roles, progress/ notes on disk, the anti–broken-telephone rule, and the real verification commands (uv run ruff/pytest, pnpm lint/test/build/playwright). Use when starting or closing a coordinated implementation task or delegating to subagents.
---

# Harness — Roles, progress notes, verification

Docket is a single-developer interview challenge. The harness is deliberately small: three roles, a folder of notes, and one verification script (`scripts/harness-verify.sh`) that runs lint and tests in small locked batches. There are no session registries or path claims.

## Roles

| Role | File | Does | Does not |
|---|---|---|---|
| leader | `.claude/agents/leader.md` | Plans, delegates, closes | Edit app code in delegated flows |
| implementer | `.claude/agents/implementer.md` | One scoped task: code + tests + docs + verification | Self-approve |
| reviewer | `.claude/agents/reviewer.md` | Re-runs verification, walks `.claude/CHECKPOINTS.md` | Edit code |

Trivial single-file changes and questions skip the harness.

## progress/ notes

```
progress/
  history.md                    # append-only log, one block per closed topic
  <topic>/
    plan.md                     # leader: task, scope, plan, paths per subagent
    explore_<subtopic>.md       # explorers: findings with file:line references
    impl_<subtopic>.md          # implementer: files, commands, output, open issues
    review_<subtopic>.md        # reviewer: verdict + checkpoints
```

`<topic>` is kebab-case (`ledger-excel-writer`, `inbox-batch-approve`). Create the folder on demand.

## Anti–broken-telephone

Subagents write results to disk and reply with one line:

```
done -> progress/<topic>/impl_<subtopic>.md
blocked -> progress/<topic>/impl_<subtopic>.md
APPROVED -> progress/<topic>/review_<subtopic>.md
CHANGES_REQUESTED -> progress/<topic>/review_<subtopic>.md
```

## Working next to other agents

Another agent may be editing the tree (often `backend/`) at the same time.

- Every subagent gets an explicit list of paths it may write. Parallel subagents get disjoint paths.
- Re-read a file right before editing; make targeted edits; never revert or reformat lines you did not write.
- A failing test in a file you did not touch may be someone else's work in progress: re-run it alone, then report it instead of "fixing" it.

## Verification (required before "done") — chunked, never one big run

**NEVER run a test suite in one go or with unbounded parallelism** — frontend (bare `pnpm test`, `npx jest`, `jest --watch`, high `--maxWorkers`) or backend (bare `uv run pytest` over the whole tree, `pytest -n auto`/xdist, `--looponfail`): it saturates the machine's RAM. All tests go through `./scripts/harness-verify.sh`.

```bash
./scripts/harness-verify.sh [--backend|--frontend|--e2e|--all] [--changed | --full | <test paths...>] [--batch N]
```

| Scope | Command |
|---|---|
| backend | `./scripts/harness-verify.sh --backend` |
| frontend | `./scripts/harness-verify.sh --frontend`, then `cd frontend && pnpm build` |
| e2e | `./scripts/harness-verify.sh --e2e` |
| cross-stack | `./scripts/harness-verify.sh --all` |
| one file | `./scripts/harness-verify.sh backend/tests/features/ledger/test_assign_filing_number.py` |
| whole suite | `./scripts/harness-verify.sh --all --full` — **only when the user explicitly asks** |

What the script does:

- `--changed` (default): files from `git diff --name-only HEAD` + untracked. Backend `backend/app/features/<slice>/**` -> `backend/tests/features/<slice>/test_*.py` (+ `backend/tests/golden/`); `backend/app/shared/**` -> `backend/tests/shared/` (+ golden); `backend/app/mcp/**` -> `backend/tests/mcp/`. Frontend `frontend/src/features/<f>/**` -> tests under that feature; `frontend/src/shared/**` -> tests under `shared/`. Changed test files map to themselves; changed `frontend/e2e/*.spec.ts` run as e2e.
- Lint first: `uv run ruff check` on changed backend files; `pnpm lint` only when frontend files changed (skipped while `frontend/package.json` does not exist).
- Batches of `--batch N` files (default 3), one at a time: `uv run pytest -q -p no:cacheprovider <files>`, `pnpm exec jest --maxWorkers=1 <files>`, `pnpm exec playwright test --workers=1 <specs>`.
- Per-runner lock (`${TMPDIR}/docket-locks/{pytest,jest,playwright}.lock`, waits up to `DOCKET_LOCK_TIMEOUT_SEC`=600) so parallel agents never stack test processes.
- RAM guard before each batch: aborts if free memory stays under `DOCKET_MIN_FREE_MEM_PCT` (15) after `DOCKET_RAM_RETRIES` waits.
- Stops at the first red batch, prints a summary, exits non-zero on failure.

Record the exact commands and the summary in `impl_<subtopic>.md`; "no tests selected" for changed logic is not a pass — add the missing tests.

## Close

1. Reviewer verdict `APPROVED` (includes bilingual feature docs in `docs/en/` and `docs/es/`).
2. Leader appends to `progress/history.md`: date, topic, files, commands, outcome.
3. No `git commit` / `push` / `stash` / branch changes unless the user asks.
