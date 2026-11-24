---
name: testing-web
description: Enforces behavior-first frontend testing for Docket — Jest + React Testing Library per feature __tests__/, Playwright E2E for the core flows, all run in chunks through ./scripts/harness-verify.sh (never a bare pnpm test). Use when writing or running frontend tests or adding test coverage in frontend/.
---

# Skill — Frontend testing (Jest + RTL, Playwright)

## Policy

- Behavior changes require tests; bug fixes require a regression test.
- Test what the user sees (roles, labels, Spanish text), not implementation details.
- Mock the network at `features/<f>/api` or `shared/lib/api-client` boundaries; keep mappers and components real.

## What to test

| Change | Test | Location |
|---|---|---|
| Mapper, helper, zod schema | Jest unit | `features/<f>/__tests__/`, `shared/lib/__tests__/` |
| Component (loading/empty/error/success, interactions) | Jest + RTL | `features/<f>/__tests__/<Name>.test.tsx`, `shared/ui/<layer>/__tests__/` |
| Hook | Jest + `renderHook` | `features/<f>/__tests__/use<Name>.test.ts` |
| i18n dictionaries | every code has a label | `shared/i18n/__tests__/` |
| User flow | Playwright | `frontend/e2e/<flow>.spec.ts` |

Minimum per change: happy path, failure path (API error code shown in Spanish), edge/empty state.

Core E2E flows: import the inbox; see e-mail 05 held for verification with its reason; correct a document; batch-approve `READY` documents; download the Excel; see this week's deadlines (oversight notice due 2026-11-23 urgent, petition due 2026-11-27).

## Running tests: chunked through the harness only (HARD RULE)

**NEVER** run bare `pnpm test`, `npx jest`, `jest --watch` or a high `--maxWorkers`: it saturates the machine's RAM.

```bash
./scripts/harness-verify.sh --frontend                      # pnpm lint + jest batches for changed features (--maxWorkers=1)
./scripts/harness-verify.sh frontend/src/features/inbox/__tests__/InboxTable.test.tsx
./scripts/harness-verify.sh --e2e                           # changed Playwright specs, --workers=1
./scripts/harness-verify.sh --frontend --full               # whole suite, chunked: only when the user asks
cd frontend && pnpm build                                   # type and build check
```

Keep tests inside the feature (`features/<f>/**`) or `shared/**` so `--changed` finds them. Playwright config sets `workers: 1` and `fullyParallel: false`. Report which batches ran.

## If tooling is missing

Add the minimal setup (jest config with `next/jest`, RTL, `@testing-library/jest-dom`, Playwright config) in the same task; do not skip tests silently.

## Done when

- Changed behavior covered (happy / failure / edge).
- `./scripts/harness-verify.sh --frontend` and `--e2e` green; `pnpm build` green.
- "How it is tested" updated in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`.
