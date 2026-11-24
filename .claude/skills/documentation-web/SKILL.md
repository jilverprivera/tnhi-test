---
name: documentation-web
description: Enforces Docket's mandatory bilingual feature documentation — every shipped feature (backend slice or frontend feature) has Markdown docs in both docs/en/features/<slug>.md and docs/es/features/<slug>.md with the same structure, indexed in docs/en/README.md and docs/es/README.md. Provides the template. Use when implementing or changing any feature, or when asked to document how part of the app works.
---

# Skill — Bilingual feature documentation (mandatory)

## Rule (HARD)

**Every feature the system ships must come with documentation of how that part of the app works, written in Markdown in BOTH English and Spanish, under the repository-root `docs/` folder.** A feature without both docs updated is not done; the reviewer rejects it.

## Layout

```
docs/
  en/
    README.md                     # index: deliverables + feature docs
    features/<feature-slug>.md
  es/
    README.md                     # índice
    features/<feature-slug>.md
```

- `<feature-slug>` = the feature folder name: backend slices `ingestion`, `classification`, `filing`, `ledger`, `deadlines`, `catalogs`, `audit`, plus `mcp` (the read-only MCP server); frontend features `inbox`, `document-review`, `ledger`, `deadlines`, `settings`; cross-cutting `pwa` (see `documentation-mobile`). When a backend slice and a frontend feature share a slug (`ledger`, `deadlines`), one doc covers both sides.
- Same slug, same headings, same order in both languages. Spanish file uses Spanish headings with the same meaning.
- `docs/en/` and `docs/es/` also hold the interview deliverables (executive summary, architecture, features, solution, domain model, quality attributes); the README lists them too.
- Code identifiers, endpoints and codes stay in English inside the Spanish docs (they are names, not prose).

## Template (`docs/en/features/<slug>.md`)

```markdown
# <Feature name>

## Purpose
What problem it solves for TAC.

## Who uses it
Clerk (CLERK), coordinator (COORDINATOR), AI assistant via MCP — and for what.

## How it works
Step-by-step flow; a Mermaid diagram when the flow has branches.

## Business rules
Each rule with its source (interview quote / client data) and where it lives in code.

## API endpoints / screens
Endpoints (method, path, request/response keys) and/or routes and main components.

## Codes
| Code | Meaning (EN) | Significado (ES) | Blocking? |
|---|---|---|---|
| `EMAIL_ACCOUNT_MISMATCH` | The e-mail asks to pay into an account that differs from the supplier master | El correo pide consignar a una cuenta distinta a la del maestro de proveedores | Yes |

## Limitations
Known gaps and technical debt.

## How it is tested
Test files, golden cases, E2E specs, and the harness command that runs them.
```

Spanish headings for `docs/es/features/<slug>.md`: Propósito, Quién lo usa, Cómo funciona, Reglas de negocio, Endpoints / pantallas, Códigos, Limitaciones, Cómo se prueba.

## Updating

- New endpoint, screen, rule or code -> update the matching sections in both languages in the same change.
- Changed behavior -> update both; never let them drift.
- New feature -> create both files and add them to both READMEs.

## Checklist

- Both `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md` exist and match in structure?
- All codes the feature emits listed with EN and ES meaning?
- Endpoints/screens and "How it is tested" current?
- Both READMEs list the doc?
