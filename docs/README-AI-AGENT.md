# Agent Context & Technical Notes (`README-AI-AGENT.md`)

Technical guide and critical invariants for AI coding agents working in **TrueHDR Photo Converter**.

---

## 1. Project Domain & Invariants

- **Domain:** Desktop and CLI photographic image converter specializing in True HDR (10-bit / 16-bit Rec.2020 PQ, ISO 21496-1 Gain Maps, linear Rec.2020 OpenEXR) and SDR processing.
- **Critical Non-Negotiables:**
  - **Zero Data Loss:** Never overwrite original input images. Work is done strictly in `output/`.
  - **No Silent Failures:** Never catch exceptions silently. Always log warnings or record diagnostic failures.
  - **Git Boundaries:** The user commits and pushes manually via GitHub Desktop. Never run `git init`, `add`, `commit`, or `push`.
  - **Headless-First:** All business logic in `python_encoders.py`, `exr_encoder.py`, `converter.py`, `classifier.py`, and `renamer.py` must run without GUI / Qt.
  - **Correct HDR Signaling & ICC Preservation:**
    - HEIC HDR (`pillow-heif`): 10-bit 4:2:0, `color_primaries=9`, `transfer_characteristics=16` (PQ), `matrix_coefficients=9`, `full_range_flag=1`, preserve ICC.
    - AVIF HDR (`imagecodecs.avif_encode`): 10-bit 4:2:0, CICP `9/16/9`, `tilelog2=(2, 2)`, `numthreads=os.cpu_count()`, preserve ICC.
    - AVIF SDR (`imagecodecs.avif_encode`): 8-bit 4:2:0, CICP `1/13/1`, preserve ICC.
    - Ultra HDR JPEG (`imagecodecs.ultrahdr_encode` + `ultrahdr_encode_jpeg`): Rec.2020 linear half-float (`1.0 == 203 nits`), pre-encoded optimized 4:2:0 SDR base with ICC.
    - EXR (`OpenEXR 3.5.5`): HDR-only, runs independently of `HDR/PQ` and `HDR/GainMap` checkboxes, Rec.2020 `chromaticities`, `whiteLuminance = 203.0`, default `lj2k`.
  - **PyInstaller Gotchas:**
    - `imagecodecs` uses dynamic Cython imports (`_shared`, `_shared_cython`, `_imcd`, `_png`, `_jpeg`, `_avif`, `_ultrahdr` — note `_jpeg`, **not** `_jpeg8`!), and `OpenEXR` needs `Imath` in `HIDDEN_IMPORTS`.
    - Do not reintroduce `opencv-python` (`cv2` adds ~112 MiB unpacked); decode 8/16-bit PNGs via `imagecodecs.png_decode(path.read_bytes())` (Unicode-safe by default).
    - Use `--add-data` (not `--add-binary`) for `bin/` in `--onefile` so `cjxl.exe` and its companion DLLs stay together in `_MEIPASS/bin/`.
    - Portable `--onedir` builds auto-detect portable mode via `(exe_dir / "_internal").is_dir()`, so `data/settings.json` is never pre-bundled into the ZIP.

---

## 2. Source Code Map

| File                     | Primary Responsibility                                        | Key Symbols                                                                |
| ------------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `src/main.py`            | Main entry point                                              | `main()`                                                                   |
| `src/cli.py`             | Headless CLI interface                                        | `run_cli()`, `build_parser()`                                              |
| `src/gui.py`             | PySide6 main window                                           | `MainWindow`, `run_gui()`                                                  |
| `src/summary_dialog.py`  | Modal completion summary                                      | `ProcessingSummaryDialog`, `build_summary_view_model()`                    |
| `src/models.py`          | Data contracts & constants                                    | `ImageType`, `AppSettings`, `EXR_COMPRESSIONS`, `compute_zero_fill()`      |
| `src/config.py`          | Config, portable mode, `bin/` PATH & tool detection           | `detect_tools()`, `load_settings_from_file()`, `logs_dir()`                |
| `src/classifier.py`      | Suffix detection & grouping                                   | `normalize_base()`, `classify_files()`                                     |
| `src/renamer.py`         | Rename planner & executor                                     | `build_rename_plan()`, `execute_rename_plan()`                             |
| `src/python_encoders.py` | Native Python codecs (`imagecodecs`, `pillow-heif`, `Pillow`) | `encode_sdr_*()`, `encode_hdr_*()`, `load_*_png()`                         |
| `src/exr_encoder.py`     | Native Python `OpenEXR 3.5.5` linear HDR encoder              | `encode_hdr_rgb16_to_exr()`, `encode_hdr_png_to_exr()`, `recompress_exr()` |
| `src/converter.py`       | Unified conversion orchestrator & retries                     | `convert_sdr()`, `convert_hdr()`, `ProcessRunner`                          |
| `src/worker.py`          | Pipeline execution worker                                     | `ProcessingWorker`                                                         |
| `src/results.py`         | Outcome models & counters                                     | `ProcessingSummary`, `ProcessingOutcome`                                   |
| `tools/build_exe.py`     | PyInstaller `--onefile` + portable `--onedir` ZIP builder     | `build_onedir()`, `build_onefile()`                                        |
