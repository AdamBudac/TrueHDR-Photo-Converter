# 🗺️ Implementačný plán (`IMPLEMENTATION_PLAN.md`)

Prehľad schválených etáp, aktuálneho stavu a overených výsledkov projektu **TrueHDR Photo Converter**.

---

## Etapa 1 – Stabilizácia kodekov, auditu a living dokumentácie (`2026-11-23`)

Stav: **dokončené a overené**

- [x] Prvotný audit a uzavretie všetkých nálezov (`AUD-001` až `AUD-010`)
- [x] Analýza referenčných súborov z Lightroomu a Photoshopu (SDR sRGB vs. HDR Rec.2020 PQ 10/16-bit, EXR PIZ)
- [x] Oprava HDR HEIC PQ (`transfer_characteristic=16`), odstránenie `--ignore-icc`, oprava SDR AVIF CICP (`1/13/1`), čistá suffixová schéma (`_BW`, `_HDR`, `_BW_HDR`), `pytest.ini`, zerofill 1–99, logy v `logs/`
- [x] Zjednotenie a migrácia living dokumentácie a odstránenie `.old` súborov

## Etapa 2 – HDR/PQ, HDR/GainMap, OpenEXR a GUI ergonómia (`2026-11-23`)

Stav: **dokončené a overené**

- [x] Nová GUI sekcia **SDR/HDR processing** (`SDR`, `HDR/PQ`, `HDR/GainMap`), presné zarovnanie `Settings` ↔ `Codecs`, checkbox `Add space` (`space_after_prefix`) a predvolený prefix `Image`
- [x] Suffixy `_HDR-PQ` a `_HDR-GM`, Rec.2020 PQ Ultra HDR JPEG (párový aj Scenario 0 fallback) a ISO 21496-1 AVIF Gain Map
- [x] Jednorazové spúšťanie `_HDR-PQ.jxl` a `_HDR-PQ.heic` pri zapnutom aspoň jednom HDR režime
- [x] Natívny Python `OpenEXR 3.5.5` enkóder (`EXR (HDR only)`, nezávislý od `HDR/PQ` a `HDR/GainMap`, všetkých 14 kompresií, default `LJ2K`, Rec.2020 `chromaticities`, `whiteLuminance = 203.0`)

## Etapa 3 – Natívne Python enkódery a Windows Release balíky (`2026-11-23`)

Stav: **dokončené a overené**

- [x] Prechod na natívne Python knižnice (`imagecodecs 2026.11.11`, `pillow-heif 1.8.1`, `OpenEXR 3.5.5`, `Pillow 13.0.0`, `numpy 2.5.5`) – 4:2:0 Ultra HDR JPEG Scenár 3, viacvláknový AVIF (`tilelog2=(2, 2)`, `os.cpu_count()`)
- [x] Priečinok `bin/` (`avifgainmaputil.exe` + `cjxl.exe` a DLL) prioritizovaný v `PATH`
- [x] `tools/build_exe.py` generujúci oba release balíky: `dist/TrueHDRPhotoConverter.exe` (`--onefile`) aj prenosný `dist/TrueHDRPhotoConverter/` + `dist/TrueHDRPhotoConverter.zip` (`--onedir`)
- [x] Kompletná synchronizácia dokumentácie (EN/SK/CZ), `AGENTS.md`, `.gitignore` a `.gitattributes`

### Výsledky overenia

- `2026-11-23`: `python -m pytest -v` → **48/48 testov prešlo**.
- `2026-11-23`: Overené konverzie 6000×4000 v `temp/conversions/` a `temp/conversions/python/` cez `ffprobe`, `OpenEXR` aj `ultrahdr_app -m 1 -P`, plus vizuálne overenie v galérii.
- `2026-11-23`: Overené samostatné spustenie a kompletná 10-výstupová konverzia z `dist/TrueHDRPhotoConverter.exe` aj prenosného `dist/TrueHDRPhotoConverter/TrueHDRPhotoConverter.exe` v izolovanom `PATH = C:\Windows\System32`.
