---
name: architecture-web
description: Enforces the Docket frontend architecture — Next.js App Router with screaming architecture (features first: inbox, document-review, verifications, ledger, deadlines, settings, compliance, session) plus atomic design in shared/ui, thin routes, feature api/hooks/model layers, and the shared api client. Use when adding or changing routes, features, hooks, API calls, state, or any architectural decision in web/.
---

# Skill — Frontend architecture (Next.js + features + atomic design)

## Goal

Opening `web/src/features/` should tell you what Docket does. Routes are thin, features own their code, shared UI is a small design system.

## Layout

```
web/src/
  app/                          # routes only
    layout.tsx                  # html shell, theme, fonts, PWA metadata
    page.tsx                    # redirect
    login/page.tsx  offline/page.tsx
    (app)/layout.tsx            # AppShell for signed-in screens
    (app)/inbox/page.tsx        # composes features/inbox template
    (app)/documents/[id]/page.tsx
    (app)/ledger/page.tsx
    (app)/deadlines/page.tsx
    (app)/settings/page.tsx
    (app)/verifications/page.tsx   # coordinator's held invoices
    (app)/compliance/page.tsx      # coordinator's retention (TRD) and habeas data
    (app)/error.tsx             # error boundary: retry / sign in again
    files/documents/[id]/route.ts  files/ledger/route.ts   # route handlers streaming the original file / Excel from the API
    manifest.ts  sw.ts          # PWA (see architecture-mobile)
  proxy.ts                      # route guard: no `docket_token` cookie -> /login
  features/<feature>/
    components/
      molecules/ organisms/ templates/   # feature-specific UI
    hooks/                      # client hooks (currently empty in inbox/ and document-review/)
    api/                        # <f>-queries.ts (server reads: fetchInbox, fetchDocument, ...) and
                                # <f>-actions.ts ("use server" Server Actions: approveDocumentAction, ...)
    model/                      # types.ts (*View view models) + mappers.ts (<Thing>Response -> *View) + schemas.ts (zod)
    __tests__/                  # Jest + RTL tests for this feature
    index.ts                    # public barrel: templates + what routes need
  shared/
    ui/
      primitives/               # shadcn/ui generated (kebab-case files)
      atoms/ molecules/ organisms/ templates/
    lib/                        # api-client.ts (server-only), api-error.ts, api-types.ts (raw <Thing>Response types), session.ts, format.ts, cn.ts
    i18n/es.ts                  # Spanish labels for UPPER_SNAKE codes and UI copy
    theme/tokens.css            # Tailwind v4 @theme tokens (see theme-web)
web/e2e/                   # Playwright specs (config: web/playwright.config.ts)
```

Features: `inbox` (queue with traffic-light status, filters, URL-based pagination with `shared/ui/molecules/Pagination.tsx`, queued import followed by polling, batch approve of `READY`), `document-review` (original viewer + extracted fields + reasons/evidence + audit timeline, approve/correct/discard; `EscalateHoldButton` for suspected fraud), `verifications` (coordinator's held invoices: arrived vs supplier master, release / confirm fraud with a required note), `ledger` (search, duplicates, Excel download), `deadlines` (this week / next / overdue, urgent highlighted, weekly report), `settings` (system status, supplier master upload, outbox preview), `compliance` (TRD table, due records + `DisposeButton`, personal data inventory, `SubjectRequestForm`), `session` (login/logout, role-based nav).

Role-based navigation: `shared/ui/organisms/AppNav.tsx` owns `ROLE_NAV` (CLERK: inbox, deadlines, ledger, settings; COORDINATOR: deadlines, verifications, ledger, inbox, compliance) and `ROLE_HOME` (CLERK `/inbox`, COORDINATOR `/deadlines`); `features/session/components/organisms/SessionNav.tsx` picks the items from the session role, and `loginAction` redirects to `ROLE_HOME` of the role the API returns. A new screen for one role goes into that role's `ROLE_NAV` entry; the API still enforces the permission.

## Rules (HARD)

- Domain code lives in `features/<feature>/`. Nothing feature-specific in `shared/`.
- **No feature imports another feature.** If two features need something, move it to `shared/` (UI to `shared/ui`, helpers to `shared/lib`).
- Routes in `app/` only read params, fetch on the server when possible, and render one feature template. No business logic, no direct `fetch`.
- Atomic order `primitives -> atoms -> molecules -> organisms -> templates`; never import upward. Features have no atoms: feature atoms belong in `shared/ui/atoms`.
- Routes import from the feature barrel (`@/features/inbox`), never deep paths.

## Data flow

1. `features/<f>/api/*.ts` call `shared/lib/api-client.ts` (`import "server-only"`; `api<T>()` typed `fetch` wrapper: base URL from the server-side `DOCKET_API_URL`, JSON, returns the `{code, data}` envelope; error body `{code, detail}` -> `ApiError` with the `UPPER_SNAKE_CASE` code; auth token from the httpOnly `docket_token` cookie as `Authorization: Bearer`, so it never reaches the browser).
2. `model/mappers.ts` convert `snake_case` `<Thing>Response` types into `camelCase` view models.
3. Server Components fetch read views (`*-queries.ts`); mutations are Server Actions in `*-actions.ts` returning `ActionResult` (`{ok, code}`) and calling `refresh()` from `next/cache`; client components invoke them inside `useTransition`.
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
