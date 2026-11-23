# TrueHDR Photo Converter

[English](../README.md) | [Slovenčina](./README-SK.md) | **Čeština**

Výkonná desktopová (PySide6 GUI) a CLI automatizační aplikace pro Windows pro konverzi, přejmenování a třídění SDR (8-bit sRGB) a True HDR (16-bit Rec.2020 PQ) fotografií (PNG, EXR, HDR JPEG) do moderních formátů: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL (JXL)**, **HEIC**, **AVIF (PQ & Gain Map)** a **OpenEXR (HDR)**.

---

## Hlavní funkce

- **Oddělené zpracování `SDR`, `HDR/PQ` a `HDR/GainMap`:** Samostatné přepínače v sekci **SDR/HDR processing** s nedestruktivním zpracováním do podsložky `output/`.
- **Moderní sada kodeků (nativní Python + přibalené `cjxl` a `avifgainmaputil`):**
  - **JPEG & Ultra HDR JPEG (`_HDR-GM.jpg`):** 8-bit 4:2:0 sRGB přes `imagecodecs` (`libjpeg-turbo 3.2.1`) a ISO 21496-1 Rec.2020 PQ Ultra HDR Gain Map (`libultrahdr 2.0.2`, 4:2:0 základ se zachovaným ICC; párový SDR+HDR PNG i HDR-only auto-SDR fallback).
  - **JPEG XL (`_HDR-PQ.jxl`):** Ztrátové VarDCT (`--modular 0 --gaborish 1 --brotli_effort 11`) přes přibalený `cjxl` (`libjxl 0.13.0`) s Rec.2020 PQ signalizací.
  - **HEIC (`_HDR-PQ.heic`):** 8-bit SDR a 10-bit 4:2:0 Rec.2020 SMPTE ST 2084 PQ přes `pillow-heif` (`libheif 1.23.6` + `x265 4.3`) se zachovaným ICC.
  - **AVIF (`_HDR-PQ.avif` & `_HDR-GM.avif`):** Vícevláknový 8-bit BT.709 sRGB a 10-bit 4:2:0 Rec.2020 PQ přes `imagecodecs` (`libavif 1.4.2` / `aom 3.15.3`) + ISO 21496-1 AVIF Gain Map přes přibalený `avifgainmaputil`.
  - **EXR (HDR only, `_HDR.exr`):** Nativní Python `OpenEXR 3.5.5` lineární 16-bit half-float enkodér (Rec.2020 `chromaticities`, `whiteLuminance = 203.0`) se všemi 14 kompresemi (výchozí `LJ2K`), nezávislý na `HDR/PQ` a `HDR/GainMap`.
- **Flexibilní přejmenování a bezpečný běh:** Prefix, volba mezery (`Add space`), počítadlo, auto/manuální zerofill (1–99 číslic), opakování selhaných kroků a přehledné logy (`logging.log`, `rename.log`, `errors.log`).

---

## Stažení a rychlý start

### Možnost A — Hotové balíky pro Windows (bez instalace Pythonu)

Stáhněte si z **GitHub Releases**:
1. **`TrueHDRPhotoConverter.exe` (jeden soubor / onefile):** Jediný spustitelný soubor (~88 MiB) se vším uvnitř; nastavení se ukládá do `%APPDATA%\TrueHDRPhotoConverter\`.
2. **`TrueHDRPhotoConverter.zip` (přenosná verze / portable onedir):** Rozbalte složku `TrueHDRPhotoConverter/` kamkoli a spusťte `TrueHDRPhotoConverter.exe` — okamžitý start (`<1 s`), přibalený `bin/` a automatický přenosný režim (`data/settings.json` + `data/logs/`).

### Možnost B — Spuštění ze zdrojových kódů (Python)

```powershell
# Instalace závislostí (Python 3.13.17)
pip install -r requirements.txt

# Spuštění GUI
python src/main.py

# Spuštění CLI
python src/main.py --cli --input ./photos --prefix "Foto" --quality-jpeg 95 --overwrite

# Spuštění testů a sestavení release balíků
python -m pytest -v
python tools/build_exe.py
```

---

## Dokumentace

- **[Uživatelská příručka (CZ)](./README-USER-CZ.md)** · [English](./README-USER.md) · [Slovenčina](./README-USER-SK.md)
- **[Vývojářská příručka (EN)](./README-DEVELOPER.md)** · **[Specifikace (EN)](./SPEC.md)** · **[Tech Stack (EN)](./TECH-STACK.md)**
- **[Agentický kontext (EN)](./README-AI-AGENT.md)** · **[Implementační plán (SK)](./IMPLEMENTATION_PLAN.md)** · **[Audit (SK)](./AUDIT.md)** · **[Výzkum (SK)](./RESEARCH.md)** · **[Historie změn (SK)](./CHANGELOG.md)**
