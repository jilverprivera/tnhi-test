---
name: testing-web
description: Enforces behavior-first frontend testing for Docket — Jest + React Testing Library per feature __tests__/, Playwright E2E for the core flows, all run in chunks through ./scripts/harness-verify.sh (never a bare pnpm test). Use when writing or running frontend tests or adding test coverage in web/.
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
| User flow | Playwright (`web/playwright.config.ts`, projects `desktop` and `phone`) | `web/e2e/<flow>.spec.ts` (e.g. `filing-flow.spec.ts`, `mobile.spec.ts`) |

Minimum per change: happy path, failure path (API error code shown in Spanish), edge/empty state.

`shared/lib/api-client.ts` is `server-only`; Jest maps `server-only` to `web/jest.server-only.ts`, and Server Actions (`*-actions.ts`) are tested by mocking `api()`.

Core E2E flows: import the inbox; see e-mail 05 held for verification with its reason; correct a document; batch-approve `READY` documents; download the Excel; see this week's deadlines (oversight notice due 2026-11-23 urgent, petition due 2026-11-27).

## Running tests: chunked through the harness only (HARD RULE)

**NEVER** run bare `pnpm test`, `npx jest`, `jest --watch` or a high `--maxWorkers`: it saturates the machine's RAM.

```bash
./scripts/harness-verify.sh --frontend                      # pnpm lint + jest batches for changed features (--maxWorkers=1)
./scripts/harness-verify.sh web/src/features/inbox/__tests__/mappers.test.ts
./scripts/harness-verify.sh --e2e                           # changed Playwright specs, --workers=1
./scripts/harness-verify.sh --frontend --full               # whole suite, chunked: only when the user asks
cd web && pnpm build                                   # type and build check
```

Keep tests inside the feature (`features/<f>/**`) or `shared/**` so `--changed` finds them. `web/playwright.config.ts` sets `workers: 1` and `fullyParallel: false` and starts the real API (port 8010, temp `TAC_DATA_DIR`) and `next start` (port 3100); Jest sets `maxWorkers: 1` in `web/jest.config.ts`. Report which batches ran.

## If tooling is missing

Jest (`next/jest`, jsdom, RTL, `@testing-library/jest-dom`) and Playwright are set up; do not skip tests silently.

## Done when

- Changed behavior covered (happy / failure / edge).
- `./scripts/harness-verify.sh --frontend` and `--e2e` green; `pnpm build` green.
- "How it is tested" updated in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`.
