# TrueHDR Photo Converter

**English** | [Slovenčina](./docs/README-SK.md) | [Čeština](./docs/README-CZ.md)

High-performance Windows desktop (PySide6 GUI) and headless CLI automation tool for converting, renaming, and sorting SDR (8-bit sRGB) and True HDR (16-bit Rec.2020 PQ) photographic images (PNG, EXR, HDR JPEG) into modern next-generation formats: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL (JXL)**, **HEIC**, **AVIF (PQ & Gain Map)**, and **OpenEXR (HDR)**.

---

## Key Features

- **Independent SDR / HDR-PQ / HDR-GainMap Pipelines:** Dedicated checkboxes under **SDR/HDR processing** (`SDR`, `HDR/PQ`, `HDR/GainMap`) with non-destructive processing inside `output/`.
- **Modern Codec Suite (Native Python + Bundled `cjxl` / `avifgainmaputil`):**
  - **JPEG & Ultra HDR JPEG (`_HDR-GM.jpg`):** 8-bit 4:2:0 sRGB via `imagecodecs` (`libjpeg-turbo 3.2.1`) and ISO 21496-1 Rec.2020 PQ Ultra HDR Gain Map (`libultrahdr 2.0.2`, 4:2:0 primary with preserved ICC; supports both paired SDR+HDR PNG and HDR-only auto-SDR fallback).
  - **JPEG XL (`_HDR-PQ.jxl`):** Lossy VarDCT (`--modular 0 --gaborish 1 --brotli_effort 11`) via bundled `cjxl` (`libjxl 0.13.0`) with Rec.2020 PQ HDR signaling (emitted once whenever either HDR mode is enabled).
  - **HEIC (`_HDR-PQ.heic`):** 8-bit SDR and 10-bit 4:2:0 Rec.2020 SMPTE ST 2084 PQ via `pillow-heif` (`libheif 1.23.6` + `x265 4.3`) with preserved ICC profiles (emitted once whenever either HDR mode is enabled).
  - **AVIF (`_HDR-PQ.avif` & `_HDR-GM.avif`):** Multi-threaded 8-bit BT.709 sRGB and 10-bit 4:2:0 Rec.2020 PQ via `imagecodecs` (`libavif 1.4.2` / `aom 3.15.3`), plus ISO 21496-1 AVIF Gain Map via bundled `avifgainmaputil`.
  - **EXR (HDR only, `_HDR.exr`):** Native Python `OpenEXR 3.5.5` linear 16-bit half-float encoder (Rec.2020 `chromaticities`, `whiteLuminance = 203.0`) supporting all 14 official compressions (default `LJ2K`), triggered independently of `HDR/PQ` and `HDR/GainMap`.
- **Standardized Suffix & Batch Renaming Engine:**
  - SDR Color: `[Prefix][Number].[ext]` · SDR B&W: `_BW`
  - HDR/PQ: `_HDR-PQ` / `_BW_HDR-PQ` · HDR/GainMap: `_HDR-GM` / `_BW_HDR-GM` · HDR EXR/Source: `_HDR` / `_BW_HDR`
  - Prefix, automatic `Add space` separator (`space_after_prefix`), flexible starting counter, auto/manual zero-fill (1–99 digits), and collision-safe `_DuplicateXX`.
- **Fault-Tolerant Execution & Detailed Reporting:** Per-step retry (up to 2 attempts), automatic partial-file cleanup, failure isolation across codecs, modal summary dialog, and structured logs (`logging.log`, `rename.log`, `errors.log`).

---

## Download & Quick Start

### Option A — Ready-to-Run Windows Releases (No Python Required)

Download either release artifact from **GitHub Releases**:
1. **`TrueHDRPhotoConverter.exe` (Single-file EXE):** One self-contained executable (~88 MiB) — double-click and run; settings are saved in `%APPDATA%\TrueHDRPhotoConverter\`.
2. **`TrueHDRPhotoConverter.zip` (Portable Folder):** Extract `TrueHDRPhotoConverter/` anywhere and launch `TrueHDRPhotoConverter.exe` — fast instant startup (`<1 s`), self-contained `bin/` and automatic portable `data/settings.json` + `data/logs/`.

### Option B — Run from Python Source

1. Install [Python 3.13.17](https://www.python.org/)
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. *(Optional for JXL & AVIF GainMap when running from source)* Place `cjxl.exe` (+ DLLs) and `avifgainmaputil.exe` in `bin/` (or ensure `cjxl` and `avifgainmaputil` are in system `PATH`).
4. Launch GUI or CLI:

```powershell
# Launch Graphical User Interface (PySide6)
python src/main.py

# Run in headless CLI mode
python src/main.py --cli --input ./photos --prefix "Vacation" --quality-jpeg 95 --overwrite
```

### Tests & Building Release Packages

```powershell
# Run automated test suite
python -m pytest -v

# Build BOTH dist/TrueHDRPhotoConverter.exe (onefile) and dist/TrueHDRPhotoConverter.zip (portable onedir)
python tools/build_exe.py
```

---

## Project Structure

```
├── src/
│   ├── main.py             – Entry point (dispatches to GUI or CLI)
│   ├── gui.py              – PySide6 desktop GUI (MainWindow)
│   ├── cli.py              – Headless CLI parser and runner
│   ├── models.py           – Data contracts, ImageType enum, settings defaults
│   ├── config.py           – Settings persistence (portable/AppData), PATH & tool detection
│   ├── classifier.py       – Suffix-based image classification (SDR/HDR, Color/BW)
│   ├── renamer.py          – Rename plan builder and executor
│   ├── python_encoders.py  – Native Python encoders (imagecodecs, pillow-heif, Pillow)
│   ├── exr_encoder.py      – Native Python OpenEXR 3.5.5 linear HDR encoder
│   ├── converter.py        – Unified encoder orchestrator, retries, and error diagnostics
│   ├── worker.py           – Background QThread execution worker
│   ├── results.py          – Diagnostic and summary models
│   ├── summary_dialog.py   – Modal processing outcome dialog
│   └── styles.qss          – Qt style definitions
├── bin/                    – Local bundled CLI binaries (cjxl, avifgainmaputil; gitignored)
├── tests/                  – Unit, integration, retry, and Qt GUI test suite
├── docs/                   – Living documentation, user guides, specs, and changelog
└── tools/
    └── build_exe.py        – PyInstaller builder (onefile EXE + portable onedir ZIP)
```

---

## Documentation

- **[User Guide (EN)](./docs/README-USER.md)** · [Slovenčina](./docs/README-USER-SK.md) · [Čeština](./docs/README-USER-CZ.md) – End-user installation and usage guide
- **[Developer Guide (EN)](./docs/README-DEVELOPER.md)** – Architecture, development setup, testing, and release builds
- **[Product Specification (EN)](./docs/SPEC.md)** – Detailed functional specification and codec encoding rules
- **[Tech Stack & Dependencies (EN)](./docs/TECH-STACK.md)** – Pinned runtimes, Python wheels, and bundled tools
- **[AI Agent Context (EN)](./docs/README-AI-AGENT.md)** – Code map, gotchas, and project invariants
- **[Implementation Plan (SK)](./docs/IMPLEMENTATION_PLAN.md)** – Milestone tracking and verified results
- **[Open Issues / Audit (SK)](./docs/AUDIT.md)** – Living issue tracker (`AUD-XXX`)
- **[Technical Research (SK)](./docs/RESEARCH.md)** – Codec research, color spaces, and benchmarks
- **[Changelog (SK)](./docs/CHANGELOG.md)** – Verified history of changes
