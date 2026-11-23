# 📐 Product Specification (`SPEC.md`)

Comprehensive specification for **TrueHDR Photo Converter**.

---

## 1. Scope & Product Goals

- **Primary Goal:** Provide a rock-solid, automated desktop GUI and headless CLI tool to rename, sort, and encode photographic images originating from Lightroom/Photoshop into modern delivery and archival formats (JPEG, JPEG XL, HEIC, AVIF).
- **In Scope:**
  - Input formats: SDR 8-bit sRGB PNG, HDR 16-bit Rec.2020 PQ PNG, HDR EXR (companion/native), and HDR JPEG (Ultra HDR / Gain Map).
  - Encoding targets:
    - **SDR:** JPEG, HEIC, AVIF, JXL in 8-bit YUV 4:2:0 sRGB.
    - **HDR/PQ (`_HDR-PQ`):** HEIC (10-bit YUV 4:2:0 Rec.2020 PQ / SMPTE ST 2084), AVIF (10-bit YUV 4:2:0 Rec.2020 PQ), and JXL (VarDCT `--modular 0` Rec.2020 PQ / XYB).
    - **HDR/GainMap (`_HDR-GM`):** Ultra HDR JPEG (ISO 21496-1, Rec.2020 PQ via `ultrahdr_app`), AVIF Gain Map (ISO 21496-1 via `avifgainmaputil`). Combines paired SDR + HDR PNG when available (Scenario 3 / `combine`), or auto-generates a tone-mapped SDR base via `ultrahdr_app` Scenario 0 when SDR PNG is absent.
    - **HDR JXL & HEIC Triggering & Future GainMap Note:** Because `cjxl` (v0.13.0) and `heif-enc` / `libheif` (v1.23.4) + `libultrahdr` (v1.5.1) currently lack stable Windows CLI support for ISO 21496-1 Gain Maps (`tmap`), HDR JXL and HDR HEIC are each emitted **once** whenever **at least one** HDR checkbox (`HDR/PQ` or `HDR/GainMap`) is enabled, always with the `_HDR-PQ` suffix (even if triggered solely by `HDR/GainMap`). Once CLI GainMap support is available (e.g. `libultrahdr v2.x` / `libheif` `tmap` for HEIC, and future `cjxl` for JXL), each can be split into separate `_HDR-PQ` and `_HDR-GM` outputs matching AVIF.
    - **EXR (HDR only, `_HDR.exr`):** Native Python `OpenEXR 3.5.5` encoder (`src/exr_encoder.py`) converting HDR Rec.2020 PQ PNG (PQ EOTF, Rec.2020 `chromaticities`, `whiteLuminance = 203.0`) into linear 16-bit half-float OpenEXR with selectable compression ordered `none` → lossless (`rle`..`piz`) → lossy (`b44`..`lj2k`), defaulting to **`lj2k`**. Because linear EXR is neither PQ nor GainMap, it runs **independently** of the `HDR/PQ` and `HDR/GainMap` checkboxes whenever `EXR (HDR only)` is checked and HDR PNG inputs are present.
  - Renaming & Output Suffix rules:
    - SDR Color: `[Prefix][Number].[ext]`
    - SDR Black & White: `[Prefix][Number]_BW.[ext]`
    - HDR Source PNG / EXR / Companion: `[Prefix][Number]_HDR.[ext]` / `[Prefix][Number]_BW_HDR.[ext]`
    - HDR/PQ Outputs (JXL, HEIC, AVIF): `[Prefix][Number]_HDR-PQ.[ext]` / `[Prefix][Number]_BW_HDR-PQ.[ext]`
    - HDR/GainMap Outputs (JPEG, AVIF): `[Prefix][Number]_HDR-GM.[ext]` / `[Prefix][Number]_BW_HDR-GM.[ext]`
    - Duplicates: `..._DuplicateXX.[ext]`
  - Robust error recovery: Command-level retries (max 2 attempts), partial file cleanup, graceful failure isolation across codecs.
- **Non-Goals:**
  - Direct RAW development (RAW development is done in Lightroom prior to export).
  - Arbitrary video encoding or animated image sequences.

---

## 2. Image Classification & Suffix Policy

Classification is strictly suffix-driven (case-insensitive) on filename stems:

| Filename Pattern                        | Classification                   | Target Suffix              |
| --------------------------------------- | -------------------------------- | -------------------------- |
| `photo.png`                             | SDR Color                        | `Image_01.png` (no suffix) |
| `photo_BW.png`                          | SDR Black & White                | `Image_01_BW.png`          |
| `photo_HDR.png`                         | HDR Color                        | `Image_01_HDR.png`         |
| `photo_BW_HDR.png` / `photo_HDR_BW.png` | HDR Black & White                | `Image_01_BW_HDR.png`      |
| `photo_HDR.exr`                         | HDR Color (EXR)                  | `Image_01_HDR.exr`         |
| `photo_BW_HDR.exr`                      | HDR Black & White (EXR)          | `Image_01_BW_HDR.exr`      |
| `photo_HDR.jpg`                         | HDR Color (Gain Map JPG)         | `Image_01_HDR.jpg`         |
| `photo_BW_HDR.jpg`                      | HDR Black & White (Gain Map JPG) | `Image_01_BW_HDR.jpg`      |

_Note: Suffixes like `-1` or `-2` are no longer recognized as Black & White markers to prevent misclassifying numbered photo bursts._

---

## 3. Codec Encoding Specifications

All core encoders run natively in Python (`src/python_encoders.py`, `src/exr_encoder.py`) directly on in-memory NumPy arrays loaded once per PNG, while `cjxl` (for `--gaborish 1 --brotli_effort 11`) and `avifgainmaputil` (for ISO 21496-1 AVIF Gain Map) are bundled in `bin/` and embedded directly inside the PyInstaller `--onefile` EXE.

### SDR Pipeline (8-bit Input)

- **JPEG:** `imagecodecs.jpeg8_encode` (`libjpeg-turbo 3.2.1`): `level=<Q>`, `subsampling="420"`, `optimize=True`, preserves embedded ICC profile.
- **AVIF:** `imagecodecs.avif_encode` (`libavif 1.4.2` / `aom 3.15.3`): `level=<Q>`, `speed=6`, `tilelog2=(2, 2)`, `numthreads=os.cpu_count()`, `bitspersample=8`, `YUV420`, CICP `1/13/1` (BT.709 / sRGB / BT.709), preserves ICC profile.
- **HEIC:** `pillow-heif 1.8.1` (`libheif 1.23.6` / `x265 4.3`): `quality=<Q>`, `chroma=420`, NCLX `1/13/1`, `full_range_flag=1`, `preset=slow`, `tune=ssim`, `complexity=80`, preserves ICC profile.
- **JXL:** bundled `cjxl` (`libjxl 0.13.0`): `--quality <Q> --modular 0 --effort 7 --brotli_effort 11 --num_threads -1 --gaborish 1`.

### HDR Pipeline (16-bit Input, Rec.2020 PQ)

- **AVIF (`_HDR-PQ.avif`):** `imagecodecs.avif_encode` (`libavif 1.4.2` / `aom 3.15.3`): 10-bit `YUV420`, CICP `9/16/9` (BT.2020 / PQ / BT.2020 NCL), `speed=6`, `tilelog2=(2, 2)`, `numthreads=os.cpu_count()`, preserves ICC profile.
- **AVIF Gain Map (`_HDR-GM.avif`):** bundled `avifgainmaputil combine` (ISO 21496-1): pairs SDR PNG (or native Python `libultrahdr` Scenario 0 auto-SDR JPEG fallback) + HDR PNG (`--cicp-base 1/13/1`, `--cicp-alternate 9/16/9`, 8-bit 4:2:0 base & gain map).
- **HEIC (`_HDR-PQ.heic`):** `pillow-heif 1.8.1` (`libheif 1.23.6` / `x265 4.3`): 10-bit `RGB;16` input (`SAVE_HDR_TO_12_BIT=False`), `chroma=420`, NCLX `9/16/9` (Transfer Characteristic **16** PQ), `full_range_flag=1`, preserves ICC profile. Emitted once when either `HDR/PQ` or `HDR/GainMap` is enabled.
- **JXL (`_HDR-PQ.jxl`):** bundled `cjxl` (`libjxl 0.13.0`): `--quality <Q> --modular 0 --effort 7 --brotli_effort 11 --num_threads -1 --gaborish 1 -x color_space=RGB_D65_202_Rel_PeQ`. Emitted once when either `HDR/PQ` or `HDR/GainMap` is enabled.
- **Ultra HDR JPEG (`_HDR-GM.jpg`):** `imagecodecs.ultrahdr_encode` + `ultrahdr_encode_jpeg` (`libultrahdr 2.0.2`): 16-bit PQ → linear half-float RGBA (`1.0 == 203 nits`), `BT_2100`, `LINEAR`, `FULL_RANGE`, `USAGE.QUALITY`, `multichannel=True`, `scale=1`; pre-encodes optimized 4:2:0 SDR JPEG (preserving ICC profile), computes gain map against decoded 4:2:0 SDR (Scenario 3 equivalent), and packs both streams with 4:2:0 primary JPEG.
- **EXR (HDR only, `_HDR.exr`):** Native Python `OpenEXR 3.5.5` (`src/exr_encoder.py`): HDR PQ EOTF → Rec.2020 `chromaticities` (`whiteLuminance = 203.0`), linear 16-bit half-float, all 14 compressions ordered none → lossless → lossy, default `lj2k`. Triggered independently of `HDR/PQ` and `HDR/GainMap` checkboxes whenever `EXR (HDR only)` is enabled.

---

## 4. User Interface & Settings

- **Settings Persistence:**
  - Portable mode: `data/settings.json` next to executable or working directory.
  - Standard mode: `%APPDATA%/TrueHDRPhotoConverter/settings.json`.
- **Counters & Zerofill:**
  - Default prefix: `Image` (without underscore).
  - `Add space` (`space_after_prefix`, default `True`): automatically inserts a space between prefix and counter (e.g., `Image 01`, `Auto 23`) unless the prefix already ends with `" "`, `"_"`, or `"-"`.
  - Start counter: 0 to 999,999.
  - Zerofill digits: 1 to 99 (Auto or Manual mode).
- **Logs:**
  - Development logs: `logs/` in repository root.
  - Release / frozen logs: `%APPDATA%/TrueHDRPhotoConverter/logs/` or `data/logs/`.
  - Batch execution logs: `output/logging.log`, `output/rename.log`, `output/errors.log`.
