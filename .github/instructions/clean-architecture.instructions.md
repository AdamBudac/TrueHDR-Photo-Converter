---
applyTo: "**"
description: Clean architecture, layered boundaries, headless-first design, pragmatic engineering principles, and GUI responsiveness guardrails.
---

# Clean Architecture & Engineering Standards

1. **Layered Boundaries & No Reverse/Circular Dependencies:**
   - Maintain strict separation of responsibilities across layers (e.g., `core/`, `utils/`, `services/`, `data/`, `ui/`, `cli/`).
   - Lower layers (`core`, `utils`, `data`, `services`, `automation`, `scheduler`) must **never import UI/presentation modules**.
   - Place shared data contracts and configuration types in neutral, dependency-free modules to prevent circular imports.
2. **Headless-First Design:**
   - All business logic, data processing, and automation must be executable and testable in headless/CLI mode without initializing a GUI runtime (e.g., `QApplication`).
3. **Core Architectural Separations:**
   - **Separation of Concerns (SoC):** Keep distinct domains in focused, autonomous modules; avoid monolithic god-files.
   - **Mechanism vs. Policy:** Separate low-level execution mechanisms (I/O, browser/OS drivers, DB queries) from high-level business policy, orchestration, and scheduling.
   - **Command-Query Separation (CQS):** Methods either mutate state (Command) or return data without side effects (Query) — never hide state mutations inside read queries.
   - **Interface vs. Implementation:** Communicate across boundaries through clear abstractions/facades so implementations stay testable and replaceable.
4. **Pragmatic Engineering (SOLID, KISS, DRY, YAGNI, Fail-Fast):**
   - Apply **SOLID** pragmatically alongside **KISS**, **DRY**, and **YAGNI** — prefer simple, readable, modular designs over speculative abstractions or over-engineering.
   - **Fail-Fast:** Detect invalid inputs, broken invariants, and unexpected states immediately at the boundary and surface explicit errors instead of continuing silently.
5. **GUI Responsiveness & Modularity (when the project has a GUI):**
   - **Never block the main UI thread:** Offload network requests, heavy disk/image/DB work, and automation to background workers/threads (`QThread`, async tasks, worker pools).
   - Split views, tabs, reusable components, and dialogs into separate focused modules rather than monolithic window files.
   - For large tables or lists, use model-based / virtualized rendering instead of heavy per-row widgets (e.g., `QAbstractTableModel` + `QStyledItemDelegate` instead of `setCellWidget` in Qt/PySide6).
