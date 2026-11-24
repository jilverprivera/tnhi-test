---
name: pr-description
description: Generates consistent pull request descriptions for Docket (backend, frontend, docs). Use when the user asks to "write a PR description", "generate a pull request template", "check PR standards", or "review a PR description".
---

# Skill — PR description

## Goal

Every PR states **what** changed, **why**, and **how to verify it**, so a reviewer (or the interview panel) can follow it without context.

## Rules

- Title under 70 characters, conventional commit type + scope: `feat(backend): ...`, `fix(frontend): ...`, `docs: ...`, `test(backend): ...`, `chore: ...`.
- Body in English.
- Focus on intent; do not restate obvious diff lines.
- Only create or push a PR when the user asks.

## Template

```markdown
## What?
<!-- What changed, with background. -->

## Why?
<!-- Which clerk/coordinator problem or interview requirement this addresses. -->

## How?
<!-- Slices/features touched, key use cases, adapters, rules, codes added. -->

## Testing?
<!-- Commands run and results; new tests; golden test status. -->

## Screenshots (optional)
<!-- UI changes: mobile (375 px) and desktop, light and dark. -->

## Anything else? (optional)
<!-- Follow-ups, known limitations, technical debt. -->
```

## Scope-specific items for **Testing?**

**backend**
- `./scripts/harness-verify.sh --backend` green (chunked; never a bare full pytest run); golden test 100 %
- Audit events for new mutations
- New codes `UPPER_SNAKE_CASE`, documented
- `material/` untouched; Excel format preserved

**frontend**
- `./scripts/harness-verify.sh --frontend` and `--e2e` green; `cd web && pnpm build` green
- Atomic layers and one component per file respected
- Light/dark verified; 375 / 768 / 1440 px verified
- Spanish labels added for new codes

**all features**
- Docs updated in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`

## Checklist

- Title follows `type(scope): description`?
- **Why?** explains motivation, not a restatement of **What?**
- **How?** useful to a reviewer with no context?
- Scope items addressed in **Testing?**
