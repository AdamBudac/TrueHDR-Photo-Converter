# 🧰 Tech Stack, Libraries & Tooling (`TECH-STACK.md`)

Pinned technical stack and tools for **TrueHDR Photo Converter**.

---

## 1. Core Python Runtime & Packages

| Category | Component | Pinned Version | Purpose |
|---|---|---|---|
| **Runtime** | Python | **`3.13.17` (PINNED)** | Primary application runtime |
| **GUI Framework** | `PySide6` | `6.12.0` | Modern Qt6 graphical user interface |
| **Native Codecs & PNG** | `imagecodecs` | `2026.11.11` | Bundled `libpng 1.6.59` (8/16-bit PNG decode), `libjpeg-turbo 3.2.1`, `libavif 1.4.2` (`aom 3.15.3`), `libultrahdr 2.0.2` (JPEG SDR, AVIF SDR/HDR-PQ, Ultra HDR JPEG Gain Map) |
| **Native HEIC** | `pillow-heif` | `1.8.1` | Bundled `libheif 1.23.6` + `x265 4.3` (8-bit SDR & 10-bit Rec.2020 PQ HEIC with full NCLX & ICC) |
| **Native EXR** | `OpenEXR` | `3.5.5` | Native linear 16-bit half-float HDR EXR encoding (all 14 compressions + Rec.2020 `chromaticities` + `whiteLuminance`) |
| **Arrays & ICC Metadata** | `numpy`, `Pillow` | `2.5.5`, `13.0.0` | PQ EOTF LUTs, pixel buffers, and PNG ICC profile extraction |
| **Testing** | `pytest`, `pytest-qt` | `9.2.0`, `4.5.0` | Headless unit, pipeline, and Qt bot regression tests |
| **Packaging** | `PyInstaller` | `6.22.3` | Windows `--onefile` EXE and portable `--onedir` ZIP builder |

---

## 2. Bundled CLI Tools (`bin/`, embedded into Windows Release builds)

JPEG, Ultra HDR JPEG, HEIC, AVIF (SDR & HDR-PQ), PNG decoding, and EXR run natively in Python with zero external binaries. Two minimal CLI tools are placed in `bin/` (gitignored) and automatically packaged into `dist/TrueHDRPhotoConverter.exe` and `dist/TrueHDRPhotoConverter.zip` by `tools/build_exe.py`:

| Tool | Component / Project | Minimum Tested Version | Purpose |
|---|---|---|---|
| **`avifgainmaputil.exe`** | libavif (standalone static) | `1.4.2` | ISO 21496-1 AVIF Gain Map (`_HDR-GM.avif`) |
| **`cjxl.exe`** (+ DLLs) | libjxl | `0.13.0` | Maximum-compression JPEG XL (`--gaborish 1 --brotli_effort 11 --modular 0`) |

*(Optional dev/inspection tools used for QA verification: `ffprobe` 9.1, `exrheader` 3.5.4, `ultrahdr_app`, `MediaInfo` 26.x.)*

---

## 3. Recommended IDE Extensions (VS Code / Antigravity)

- `ms-python.python` – Python Language Server and Pylance
- `ms-vscode.PowerShell` – PowerShell terminal integration
- `Google.google-antigravity` – Antigravity IDE
