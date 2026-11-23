---
name: audit-workflow
description: Manage open engineering issues in docs/AUDIT.md and migrate verified fixes to docs/CHANGELOG.md. Use when auditing code, adding a new AUD-XXX finding, updating a partial fix, or closing a verified issue.
---

# Audit Workflow (`docs/AUDIT.md` -> `docs/CHANGELOG.md`)

## Adding a New Finding

1. Inspect existing IDs in `docs/AUDIT.md` and `docs/CHANGELOG.md` so the new `AUD-XXX` ID is never reused.
2. Group the item under the relevant subsystem heading and sort by priority (`P1` -> `P2` -> `P3`).
3. Include these fields concisely (in Slovak):
   - **Stav** (`Otvorené` / `Na overenie`), **Priorita** (`P1`–`P3`), **Dôkaz** (code review, reproduction, test)
   - **Miesto** (exact file path and function/symbol)
   - **Nález** (concrete root cause and impact)
   - **Podmienka uzavretia** (objective verification criteria)

## Updating a Partial Fix

1. Keep the same `AUD-XXX` ID.
2. Remove already-solved sub-parts from `docs/AUDIT.md` so only the remaining defect and pending verification stay listed.
3. Log the completed portion and its verification evidence in `docs/CHANGELOG.md`.

## Closing a Verified Issue

1. Confirm every item in **Podmienka uzavretia** has actually been verified (tests, runtime check, or diagnostics).
2. **Delete the entire `AUD-XXX` section** from `docs/AUDIT.md` (if no items remain under a section, remove empty subheadings; if zero issues remain, keep only the document title).
3. Never renumber remaining `AUD-XXX` IDs and never keep resolved history in `docs/AUDIT.md`.
4. Record the fix, `AUD-XXX` ID, and concrete verification results in `docs/CHANGELOG.md`.
