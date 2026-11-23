# 🛠️ Developer Guide (`README-DEVELOPER.md`)

Technical guide for setting up, developing, testing, and building **TrueHDR Photo Converter**.

---

## 1. Architecture Overview

The project adheres to Clean Architecture and headless-first principles:

- `src/models.py` – Core data contracts, `ImageType`, `AppSettings`, pure mathematical helpers (zero external dependencies).
- `src/config.py` – Configuration persistence (portable `data/` vs. `%APPDATA%`), `bin/` PATH prioritization, tool detection, and logging configuration.
- `src/classifier.py` – Deterministic suffix classification and grouping (`_BW`, `_HDR`, `_BW_HDR`).
- `src/renamer.py` – Rename plan construction (`space_after_prefix`, zerofill 1–99) and collision-safe disk execution.
- `src/python_encoders.py` – Native Python encoders backed by `imagecodecs` (8/16-bit PNG decode via `libpng`, JPEG SDR, Ultra HDR JPEG 4:2:0, AVIF SDR/HDR-PQ), `pillow-heif` (HEIC SDR/HDR-PQ), and `Pillow`/`NumPy`.
- `src/exr_encoder.py` – Native Python `OpenEXR 3.5.5` linear 16-bit half-float HDR EXR encoder (all 14 compressions, Rec.2020 `chromaticities`, `whiteLuminance = 203.0`).
- `src/converter.py` – Stateless conversion orchestrator, retry runner (max 2 attempts), error isolation, and bundled `cjxl` / `avifgainmaputil` CLI calls.
- `src/worker.py` – Orchestration worker (`QThread` in GUI, synchronous call in CLI).
- `src/results.py` – Diagnostic models, step outcomes, and run summaries.
- `src/gui.py` & `src/summary_dialog.py` – PySide6 user interface and modal summary dialog.
- `src/cli.py` – Headless CLI entry point using `argparse`.

---

## 2. Development Setup

1. Verify Python version (`3.13.17`):
   ```powershell
   python --version
   ```
2. Install Python dependencies (includes native compiled wheels for JPEG, Ultra HDR JPEG, HEIC, AVIF, and OpenEXR):
   ```powershell
   pip install -r requirements.txt
   ```
3. Populate local `bin/` (gitignored) with bundled Windows CLI binaries for JXL and AVIF Gain Map:
   - `bin/avifgainmaputil.exe` (`libavif 1.4.2`, standalone static)
   - `bin/cjxl.exe` + its companion DLLs (`libjxl 0.13.0`: `jxl.dll`, `jxl_cms.dll`, `jxl_threads.dll`, `brotli*.dll`, `libpng16.dll`, `zlib1.dll`, `jpeg62.dll`, `libwebp.dll`, `libsharpyuv.dll`, `gif.dll`)

---

## 3. Running Automated Tests

Tests use a project-local temp directory configured via `pytest.ini`:

```powershell
# Run full test suite (unit, integration, retry, Qt GUI regression)
python -m pytest -v
```

---

## 4. Building Standalone Windows Releases

`tools/build_exe.py` builds both GitHub Release artifacts automatically (embedding `bin/` and required native Python Cython modules):

```powershell
# Build BOTH dist/TrueHDRPhotoConverter.exe (onefile) and dist/TrueHDRPhotoConverter.zip (portable onedir)
python tools/build_exe.py

# Or build only one target:
python tools/build_exe.py --onefile
python tools/build_exe.py --onedir
```

### Release Artifacts Produced in `dist/`
- `dist/TrueHDRPhotoConverter.exe` — Single-file EXE (`--onefile`, `bin/` extracted to `_MEIPASS/bin/` at runtime; settings in `%APPDATA%\TrueHDRPhotoConverter\`).
- `dist/TrueHDRPhotoConverter.zip` — Deflate level-9 ZIP archive of `TrueHDRPhotoConverter/` (`TrueHDRPhotoConverter.exe`, `_internal/`, `bin/`); the temporary unpacked folder is removed automatically after zipping. Portable settings (`data/settings.json`) and logs (`data/logs/`) are created automatically on first launch.
