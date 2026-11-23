# 📖 User Guide (`README-USER.md`)

**English** | [Slovenčina](./README-USER-SK.md) | [Čeština](./README-USER-CZ.md)

This guide is written for end users of **TrueHDR Photo Converter**.

---

## 1. About the Application

- Automatically classifies, renames, and converts exported SDR (8-bit sRGB) and True HDR (16-bit Rec.2020 PQ) photos (PNG, EXR, HDR JPEG) into modern formats: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL**, **HEIC**, **AVIF (PQ & Gain Map)**, and **OpenEXR (HDR)**.
- Never overwrites original files — all results are written safely into a new `output/` subfolder inside your chosen image directory.

---

## 2. Requirements & Installation

- **Operating System:** Windows 10 / Windows 11 (64-bit)
- **Other Requirements:** None when using the prebuilt Windows releases from GitHub Releases.

### Choosing a Release Package

1. **Single-file EXE (`TrueHDRPhotoConverter.exe`):**
   - Just download and double-click `TrueHDRPhotoConverter.exe` (startup takes ~3 s while the self-contained archive unpacks).
   - Settings and application logs are stored in `%APPDATA%\TrueHDRPhotoConverter\`.
2. **Portable ZIP (`TrueHDRPhotoConverter.zip`):**
   - Extract the `TrueHDRPhotoConverter/` folder anywhere (desktop, USB drive, etc.) and run `TrueHDRPhotoConverter.exe`.
   - Instant startup (`<1 s`), completely portable — settings (`data/settings.json`) and logs (`data/logs/`) stay inside the extracted folder.

---

## 3. Getting Started

1. **Select image directory:** Click **Select image directory** and choose the folder containing your exported PNG/EXR/HDR JPG photos.
2. **Configure Settings:**
   - **Rename:** Enable/disable batch renaming and set your prefix (default `Image`).
   - **Add space:** Automatically inserts a space between prefix and counter (e.g., `Vacation 01`), unless the prefix already ends with space, `_`, or `-`.
   - **Counter & Zerofill:** Set starting number and automatic or manual zero-padding (1–99 digits).
3. **Choose Codecs & Quality:**
   - Enable any combination of **JPEG**, **JPEG XL**, **HEIC**, **AVIF** (quality 0–100) and **EXR (HDR only)** (selectable compression, default `LJ2K (Lossy HTJ2K)`).
4. **Choose SDR/HDR processing modes:**
   - **SDR:** Processes standard 8-bit SDR PNG images.
   - **HDR/PQ:** Generates 10/16-bit Rec.2020 PQ outputs (`_HDR-PQ.jxl`, `_HDR-PQ.heic`, `_HDR-PQ.avif`).
   - **HDR/GainMap:** Generates ISO 21496-1 Gain Map outputs (`_HDR-GM.jpg`, `_HDR-GM.avif`) by pairing SDR + HDR PNGs (or automatic SDR tone-map fallback if SDR PNG is absent).
   - *Note:* `EXR (HDR only)` exports linear Rec.2020 `_HDR.exr` independently of `HDR/PQ` and `HDR/GainMap`.
5. **Process images:** Click **Process images** (you can click **Stop** at any time). When finished, a summary dialog shows counts and opens the `output/` folder or logs.

---

## 4. Troubleshooting (FAQ)

- **Windows SmartScreen warning on first launch:** Because the executable is unsigned, click **More info → Run anyway** (or use the Portable ZIP version).
- **Where are my converted files?** Inside `<selected directory>\output\`, along with `logging.log`, `rename.log`, and `errors.log`.
- **A single codec failed for one photo:** Processing automatically retries once and continues with all remaining codecs and photos; check `output\errors.log` for exact error details.
