---
name: ui-structure-web
description: Enforces Docket UI component placement — one component per file (zero tolerance), atomic layers in shared/ui (primitives from shadcn, atoms, molecules, organisms, templates) vs feature components, the reuse-first gate, and import direction. Use when creating, splitting, moving or extracting any component in frontend/src.
---

# Skill — UI structure (atomic design + reuse-first)

UI/UX direction comes from the user-level skills `/apple-design` and `/ui-ux-pro-max`; this skill decides **where** code goes.

## 0) One component per file (HARD RULE — zero tolerance)

A `.tsx` file declares exactly **one** React component.

Forbidden:
- Two components in one file, exported or not.
- A helper component at the bottom of a parent file.
- Mixing atomic levels in a file (an atom inside a molecule file).
- Inline `const Row = () => <tr/>` reused in JSX to dodge the rule.

Allowed in the same file: pure helpers (no JSX, no hooks), types, and `items.map((item) => <ReasonRow key=... />)` iteration where `ReasonRow` lives in its own file.

Example — wrong:

```tsx
// features/document-review/components/organisms/ReasonList.tsx
export function ReasonList({ reasons }: ReasonListProps) {
  return <ul>{reasons.map((r) => <ReasonItem key={r.code} reason={r} />)}</ul>;
}
function ReasonItem({ reason }: { reason: ReasonView }) { /* second component: violation */ }
```

Right: `features/document-review/components/molecules/ReasonItem.tsx` + `organisms/ReasonList.tsx` importing it. If `ReasonItem` were needed by `inbox` too, it would go to `shared/ui/molecules/`.

## 1) Placement decision

```
shadcn base component (Button, Dialog, Table, Sheet)?   -> shared/ui/primitives/<kebab>.tsx (generated, then themed)
Used by ONE feature?                                    -> features/<f>/components/{molecules|organisms|templates}/
Used by 2+ features, or an atom?                        -> shared/ui/{atoms|molecules|organisms|templates}/
```

Shared only with 2 real consumers (atoms excepted: atoms always live in `shared/ui/atoms`). Promote, never reach into another feature.

## 2) Layers

| Layer | Examples | May import |
|---|---|---|
| primitives | `button`, `dialog`, `table`, `sheet`, `badge` | external libs only |
| atoms | `StatusDot`, `CodeLabel`, `FilingNumber`, `DueDateText` | primitives |
| molecules | `StatusBadge`, `ReasonItem`, `EvidenceSnippet`, `FieldRow` | primitives, atoms |
| organisms | `InboxTable`, `InboxCardList`, `DocumentFieldsPanel`, `DeadlineGroup` | + molecules; may own state/hooks |
| templates | `InboxTemplate`, `DocumentReviewTemplate`, `AppShell` | all lower layers |
| routes (`app/`) | `page.tsx` | feature barrels, templates |

Never import upward. Organisms may show skeletons and error states; templates compose the page layout.

## 3) Reuse-first gate (before creating anything)

1. Search the feature's own components.
2. Search `shared/ui/{atoms,molecules,organisms,templates}`.
3. Search `shared/ui/primitives` (and whether a new variant via `cva` solves it).
4. Only then create a component in the **lowest valid layer** of the right bucket.

Extending: add optional props with defaults; existing tests and visuals must not change; if it would exceed ~8 props or conflicting modes, create a new component and say why.

## 4) Files and folders

- Components: `PascalCase.tsx`; primitives keep shadcn's `kebab-case.tsx`.
- When a component needs siblings, use a folder: `Name/Name.tsx`, `Name.types.ts`, `Name.constants.ts`, `Name.functions.ts`, `index.ts` (re-export only, no logic).
- Every exported props interface documents each prop with a one-line JSDoc.
- Each layer has an `index.ts` barrel; each feature has a top-level `index.ts`.

## 5) Inside a component

Order: hooks -> local state -> refs -> effects -> derived data and handlers -> `return`. No decorative section comments.

## Checklist

| # | Check |
|---|---|
| 1 | Exactly one component per file, no mixed levels? |
| 2 | Right bucket (primitive / feature / shared) and lowest valid layer? |
| 3 | Reuse-first gate followed? |
| 4 | Import direction respected; no cross-feature import? |
| 5 | Props documented; barrels re-export only? |
| 6 | Works at 375 / 768 / 1440 px and in light/dark? |
