---
name: documentation-mobile
description: Documentation of Docket's responsive/PWA behavior (no native app; folder name is historical) — how each feature behaves on phones, offline and when installed, plus the device support matrix, written into the mandatory bilingual feature docs under docs/en/ and docs/es/. Use when a change affects small-screen layouts, offline caching, installability or device support.
---

# Skill — Documenting mobile/PWA behavior

## Rule (HARD)

Every feature ships with bilingual docs: `docs/en/features/<feature-slug>.md` and `docs/es/features/<feature-slug>.md`, same structure, indexed in `docs/en/README.md` and `docs/es/README.md` (template in `documentation-web`). A feature is not done without both.

This skill adds what those docs must say about phones and the PWA.

## In each frontend feature doc (both languages)

Inside **How it works** (or a sub-heading "On phones and offline" / "En el celular y sin conexión"):

- Phone layout vs desktop layout (what changes, what is hidden or moved to a sheet).
- Offline behavior: which data is readable offline, how fresh it is, which actions are disabled.
- Any phone-only interaction (sticky batch bar, bottom sheet).

Inside **How it is tested**: Playwright projects and specs covering phone/tablet, offline tests.

## PWA doc

`docs/en/features/pwa.md` and `docs/es/features/pwa.md` (slug `pwa`) describe:

- Installation (Android Chrome, iOS Safari "Agregar a inicio", desktop).
- Caching strategy per route, cache names, what is never cached (mutations, original documents) and why (data stays on TAC's server).
- Update flow (new version prompt).
- Device support matrix: phone 375 px, tablet 768 px, desktop 1440 px; browsers tested.
- Lighthouse scores of the last measurement.

## Changelog

Each doc ends with a dated changelog (newest first) in both languages; never delete entries.

## Checklist

| # | Check |
|---|---|
| 1 | Phone/offline behavior described in both languages? |
| 2 | `pwa` doc updated when caching, manifest or install flow changed? |
| 3 | Device matrix and test coverage current? |
| 4 | Changelog entry added in both files? |
