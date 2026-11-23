---
applyTo: "**"
description: Rules for keeping project documentation and EN/SK/CZ README mutations synchronized, protecting private TODO.md notes, and managing the living AUDIT.md tracker.
---

# Living Documentation & Audit Rules

1. **Private Notes (`docs/TODO.md`) Are Untouchable:**
   - `docs/TODO.md` contains personal developer notes, not approved agent tasks.
   - You may read `docs/TODO.md` for context, but you must **never autonomously implement items from it** or edit it without an explicit user request.
   - Approved execution tasks belong in `docs/IMPLEMENTATION_PLAN.md`.
2. **Keep `AGENTS.md` Lean:**
   - Do not bloat `AGENTS.md` with detailed UI/product behavior or lists of unused library alternatives.
   - Put detailed product/UI requirements in `docs/SPEC.md` (English) and technical research/library comparisons in `docs/RESEARCH.md` (Slovak).
3. **Documentation Language Policy & Synchronization:**
   When functionality, architecture, configuration, or behavior changes, update only the affected documents in their designated languages:
   - **English (primary technical & public source of truth):**
     - `README.md` — top-level overview or directory structure changes; always synchronize `docs/README-SK.md` and `docs/README-CZ.md`.
     - `docs/README-USER.md` — installation, UI usage, or user-visible workflows; always synchronize `docs/README-USER-SK.md` and `docs/README-USER-CZ.md`.
     - `docs/README-DEVELOPER.md` — architecture, stack, database schema, build, or testing workflow (English only).
     - `docs/README-AI-AGENT.md` — code map, technical gotchas, invariants, and agent context (English only).
     - `docs/SPEC.md` — detailed product requirements and behavior specification (English only).
     - `docs/TECH-STACK.md` — approved languages, databases, libraries, pinned versions, and IDE extensions (English only).
   - **Slovak (internal working logs):**
     - `docs/IMPLEMENTATION_PLAN.md` — milestone status and measured verification results.
     - `docs/RESEARCH.md` — external sources, verification date, and key technical decisions.
     - `docs/CHANGELOG.md` — every logical change with actual verification results.
4. **Living Audit (`docs/AUDIT.md`, Slovak):**
   - `docs/AUDIT.md` holds **open issues only** with stable IDs (`AUD-001`, `AUD-002`, ...).
   - On partial fix, update the entry to reflect only the remaining issue and verification criteria.
   - Once completely fixed and verified, **remove the entire entry from `docs/AUDIT.md`** and record the fix, ID, and verification evidence in `docs/CHANGELOG.md`.
   - Never renumber remaining IDs and never store resolved history inside `docs/AUDIT.md`.
