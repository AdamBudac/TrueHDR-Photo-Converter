# AGENTS.md — TrueHDR Photo Converter

## 1. Project Overview

- **Name:** `TrueHDR Photo Converter` (`TrueHDR-Photo-Converter`)
- **Purpose:** Desktop GUI and headless CLI automation tool for sorting, renaming, and converting SDR (8-bit sRGB) and True HDR (16-bit Rec.2020 PQ) photographic images (PNG, EXR, HDR JPEG) into JPEG, Ultra HDR JPEG, JPEG XL, HEIC, AVIF (PQ & GainMap), and linear HDR OpenEXR.
- **Target Platform:** Windows 11 x64 desktop (PySide6 GUI + headless CLI; standalone `--onefile` EXE and portable `--onedir` ZIP)
- **UI Languages:** English (GUI/CLI); public documentation in English, Slovak, and Czech

## 2. Language Policy

- **Chat & plans:** Always communicate with the user and write plans/summaries in **Slovak**.
- **English (primary technical & public source of truth):** All source code, identifiers, comments, logs, commit messages, agent files (`AGENTS.md`, `.agents/**`, `.github/instructions/**`), `README.md`, `docs/README-USER.md`, `docs/README-DEVELOPER.md`, `docs/README-AI-AGENT.md`, `docs/SPEC.md`, and `docs/TECH-STACK.md`.
- **SK / CZ public mutations:** Keep `docs/README-SK.md`, `docs/README-CZ.md`, `docs/README-USER-SK.md`, and `docs/README-USER-CZ.md` synchronized with their English sources.
- **Slovak working logs:** Keep `docs/TODO.md`, `docs/AUDIT.md`, `docs/CHANGELOG.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/RESEARCH.md` in **Slovak**.

## 3. Core Stack

- **Language / Runtime:** Python `3.13.17`
- **Framework / UI:** PySide6 `6.12.0`
- **Codecs:** Native Python (`imagecodecs 2026.11.11`, `pillow-heif 1.8.1`, `OpenEXR 3.5.5`, `Pillow 13.0.0`, `numpy 2.5.5`) + bundled `bin/` (`cjxl.exe` 0.13.0, `avifgainmaputil.exe` 1.4.2)
- **Storage:** JSON (`%APPDATA%/TrueHDRPhotoConverter/settings.json` for onefile EXE; automatic portable `data/settings.json` for onedir ZIP)
- **Build / Test:** PyInstaller `6.22.3` (`tools/build_exe.py`), `pytest 9.2.0` + `pytest-qt 4.5.0`
- **Full Approved Stack & Tooling:** [`docs/TECH-STACK.md`](./docs/TECH-STACK.md)

## 4. Key Commands

- **Run GUI:** `python src/main.py`
- **Run CLI:** `python src/main.py --cli --input ./photos --overwrite`
- **Tests:** `python -m pytest -v`
- **Build Releases (onefile EXE + portable onedir ZIP):** `python tools/build_exe.py`

## 5. Architecture & Code Map

- `src/models.py`, `src/config.py`, `src/classifier.py`, `src/renamer.py` — Pure domain models, settings persistence, suffix classification, and renaming (zero Qt imports)
- `src/python_encoders.py`, `src/exr_encoder.py`, `src/converter.py` — Native Python + bundled CLI encoders, retry & error isolation
- `src/worker.py`, `src/results.py` — Background `QThread` pipeline orchestration and structured summaries
- `src/gui.py`, `src/summary_dialog.py`, `src/cli.py`, `src/main.py` — PySide6 GUI, modal summary, CLI entry point
- `tests/` — Unit, integration, retry, and Qt GUI regression tests (`pytest.ini` uses project-local temp)
- Detailed code map and gotchas: [`docs/README-AI-AGENT.md`](./docs/README-AI-AGENT.md)

## 6. Non-Negotiable Project Invariants

1. **Non-destructive:** Never modify or overwrite original user input files; always work on copies in `output/`.
2. **UI responsiveness:** Never block the PySide6 main thread; all I/O and encoding run inside `ProcessingWorker(QThread)`.
3. **Color fidelity:** Always preserve Rec.2020 PQ signaling (`9/16/9` for HDR AVIF/HEIC, `BT2100/PQ` for JXL, Rec.2020 `chromaticities` + `whiteLuminance=203.0` for EXR) and embedded ICC profiles; never pass `--ignore-icc` to `avifenc`.
4. **EXR is HDR-only & independent:** Linear EXR runs exclusively on HDR PNG inputs and is triggered whenever `EXR (HDR only)` is enabled, regardless of `HDR/PQ` and `HDR/GainMap` checkboxes.

## 7. Core Workspace Rules & Documentation

Detailed mandatory rules live in `.agents/rules/` (Antigravity) and `.github/instructions/` (VS Code Agent Host):
- **Clean Architecture & GUI Hygiene:** Strict layered boundaries (no reverse/circular imports into UI), headless-first domain logic, pragmatic SOLID/KISS/DRY/YAGNI/Fail-Fast.
- **Zero-Leakage Security:** Never read, print, or commit `.env*`, `.vscode/sftp.json`, `*.sql` dumps, or private keys.
- **Private Notes (`docs/TODO.md`):** Read-only for context. **Never autonomously implement items from `docs/TODO.md`** or edit it without explicit user instruction.
- **Git & GitHub Desktop Workflow:** Never run `git init`, `git add`, `git commit`, `git push`, `git rebase`, `git checkout`, `git reset`, create releases, or deploy without explicit user approval.
- **Evidence Over Assumptions:** Verify affected code after changes; distinguish planned vs. actually verified checks.
- **Living Docs:** Keep `README.md` (+ `-SK`, `-CZ`), `docs/README-USER.md` (+ `-SK`, `-CZ`), `docs/README-DEVELOPER.md`, `docs/README-AI-AGENT.md`, `docs/SPEC.md`, `docs/TECH-STACK.md`, `docs/AUDIT.md`, `docs/CHANGELOG.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/RESEARCH.md` synchronized with real changes.

## 8. MCP & Skills Discipline

- Verify actually connected MCP tools in the active session before relying on them.
- Use project skills in `.agents/skills/` (`audit-workflow`, `changelog-entry`) when applicable.
