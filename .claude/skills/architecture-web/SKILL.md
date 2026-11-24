---
name: architecture-web
description: Enforces the Docket frontend architecture — Next.js App Router with screaming architecture (features first: inbox, document-review, ledger, deadlines, settings) plus atomic design in shared/ui, thin routes, feature api/hooks/model layers, and the shared api client. Use when adding or changing routes, features, hooks, API calls, state, or any architectural decision in frontend/.
---

# Skill — Frontend architecture (Next.js + features + atomic design)

## Goal

Opening `frontend/src/features/` should tell you what Docket does. Routes are thin, features own their code, shared UI is a small design system.

## Layout

```
frontend/src/
  app/                          # routes only
    layout.tsx                  # html shell, theme, fonts, PWA metadata
    (app)/inbox/page.tsx        # composes features/inbox template
    (app)/documents/[id]/page.tsx
    (app)/ledger/page.tsx
    (app)/deadlines/page.tsx
    (app)/settings/page.tsx
    manifest.ts  sw.ts          # PWA (see architecture-mobile)
  features/<feature>/
    components/
      molecules/ organisms/ templates/   # feature-specific UI
    hooks/                      # client hooks: useInboxFilters, useApproveDocument
    api/                        # functions calling the backend via shared/lib/api-client
    model/                      # types.ts (API shapes) + mappers.ts (API -> view model)
    __tests__/                  # Jest + RTL tests for this feature
    index.ts                    # public barrel: templates + what routes need
  shared/
    ui/
      primitives/               # shadcn/ui generated (kebab-case files)
      atoms/ molecules/ organisms/ templates/
    lib/                        # api-client.ts, cn.ts, api-types.ts, dates.ts
    i18n/                       # Spanish labels for UPPER_SNAKE codes and UI copy
    theme/tokens.css            # Tailwind v4 @theme tokens (see theme-web)
frontend/e2e/                   # Playwright specs
```

Features: `inbox` (queue with traffic-light status, filters, batch approve of `READY`), `document-review` (original viewer + extracted fields + reasons/evidence, approve/correct/send to review, outbox preview), `ledger` (search, Excel download), `deadlines` (this week / next / overdue, urgent highlighted, weekly report), `settings` (holidays, catalog reload).

## Rules (HARD)

- Domain code lives in `features/<feature>/`. Nothing feature-specific in `shared/`.
- **No feature imports another feature.** If two features need something, move it to `shared/` (UI to `shared/ui`, helpers to `shared/lib`).
- Routes in `app/` only read params, fetch on the server when possible, and render one feature template. No business logic, no direct `fetch`.
- Atomic order `primitives -> atoms -> molecules -> organisms -> templates`; never import upward. Features have no atoms: feature atoms belong in `shared/ui/atoms`.
- Routes import from the feature barrel (`@/features/inbox`), never deep paths.

## Data flow

1. `features/<f>/api/*.ts` call `shared/lib/api-client.ts` (typed `fetch` wrapper: base URL from `NEXT_PUBLIC_API_URL`, JSON, error body `{code, message, params}` -> `ApiError` with the `UPPER_SNAKE_CASE` code).
2. `model/mappers.ts` convert `snake_case` API types into `camelCase` view models.
3. Server Components fetch read views (ledger, deadlines); client hooks handle mutations (approve, correct) and refresh with `router.refresh()` or local state.
4. Components receive view models; they never see raw API payloads.
5. Errors are shown with the Spanish label of the error code (`shared/i18n`), never the raw message.

## State

- Prefer URL state (search params) for filters and tabs, so views are shareable and survive reload.
- Local `useState` for UI state; lift to a feature-level React context only when 3+ levels would need prop drilling. No global store unless a real need appears.

## Server vs client

- Server Components by default. `"use client"` only for interactive leaves (forms, filters, batch selection, viewer controls).
- Never import server-only modules into client components.

## Checklist

- Code in the right feature (or truly shared)?
- No feature-to-feature import; routes thin and importing the barrel?
- API access only through `features/<f>/api` + `shared/lib/api-client`?
- View models mapped from API types; codes translated through `shared/i18n`?
- Responsive/PWA rules applied (`architecture-mobile`)?
- Tests in `features/<f>/__tests__/`; docs in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`?
