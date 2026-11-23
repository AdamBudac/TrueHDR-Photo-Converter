# TrueHDR Photo Converter

[English](../README.md) | **Slovenčina** | [Čeština](./README-CZ.md)

Výkonná desktopová (PySide6 GUI) a CLI automatizačná aplikácia pre Windows na konverziu, premenovanie a triedenie SDR (8-bit sRGB) a True HDR (16-bit Rec.2020 PQ) fotografií (PNG, EXR, HDR JPEG) do moderných formátov: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL (JXL)**, **HEIC**, **AVIF (PQ & Gain Map)** a **OpenEXR (HDR)**.

---

## Hlavné funkcie

- **Oddelené spracovanie `SDR`, `HDR/PQ` a `HDR/GainMap`:** Samostatné prepínače v sekcii **SDR/HDR processing** s nedeštruktívnym spracovaním do podpriečinka `output/`.
- **Moderná sada kodekov (natívny Python + pribalené `cjxl` a `avifgainmaputil`):**
  - **JPEG & Ultra HDR JPEG (`_HDR-GM.jpg`):** 8-bit 4:2:0 sRGB cez `imagecodecs` (`libjpeg-turbo 3.2.1`) a ISO 21496-1 Rec.2020 PQ Ultra HDR Gain Map (`libultrahdr 2.0.2`, 4:2:0 základ so zachovaným ICC; párový SDR+HDR PNG aj HDR-only auto-SDR fallback).
  - **JPEG XL (`_HDR-PQ.jxl`):** Stratové VarDCT (`--modular 0 --gaborish 1 --brotli_effort 11`) cez pribalený `cjxl` (`libjxl 0.13.0`) s Rec.2020 PQ signalizáciou (exportuje sa raz pri zapnutom aspoň jednom HDR režime).
  - **HEIC (`_HDR-PQ.heic`):** 8-bit SDR a 10-bit 4:2:0 Rec.2020 SMPTE ST 2084 PQ cez `pillow-heif` (`libheif 1.23.6` + `x265 4.3`) so zachovaným ICC (exportuje sa raz pri zapnutom aspoň jednom HDR režime).
  - **AVIF (`_HDR-PQ.avif` & `_HDR-GM.avif`):** Viacvláknový 8-bit BT.709 sRGB a 10-bit 4:2:0 Rec.2020 PQ cez `imagecodecs` (`libavif 1.4.2` / `aom 3.15.3`) + ISO 21496-1 AVIF Gain Map cez pribalený `avifgainmaputil`.
  - **EXR (HDR only, `_HDR.exr`):** Natívny Python `OpenEXR 3.5.5` lineárny 16-bit half-float enkóder (Rec.2020 `chromaticities`, `whiteLuminance = 203.0`) so všetkými 14 kompresiami (predvolená `LJ2K`), spúšťa sa nezávisle od `HDR/PQ` a `HDR/GainMap`.
- **Prehľadná schéma prípon a premenovania:**
  - SDR farebný: bez prípony · SDR čiernobiely: `_BW`
  - HDR/PQ: `_HDR-PQ` / `_BW_HDR-PQ` · HDR/GainMap: `_HDR-GM` / `_BW_HDR-GM` · HDR EXR/zdroj: `_HDR` / `_BW_HDR`
  - Prefix, automatická medzera (`Add space`), počiatočné počítadlo, auto/manuálny zerofill (1–99 číslic) a bezpečné `_DuplicateXX`.
- **Odolné spracovanie a logovanie:** Automatický opakovaný pokus (max. 2 pokusy na krok), izolácia zlyhania medzi kodekmi, modálny súhrn po dobehnutí a logy (`logging.log`, `rename.log`, `errors.log`).

---

## Stiahnutie a rýchly štart

### Možnosť A — Hotové balíky pre Windows (bez inštalácie Pythonu)

Stiahnite si z **GitHub Releases** jednu z dvoch verzií:
1. **`TrueHDRPhotoConverter.exe` (jeden súbor / onefile):** Jediný spustiteľný EXE (~88 MiB) so všetkým vnútri; nastavenia sa ukladajú do `%APPDATA%\TrueHDRPhotoConverter\`.
2. **`TrueHDRPhotoConverter.zip` (prenosná verzia / portable onedir):** Rozbaľte `TrueHDRPhotoConverter/` kamkoľvek a spustite `TrueHDRPhotoConverter.exe` — okamžitý štart (`<1 s`), viditeľný `bin/` a automatický prenosný režim (`data/settings.json` + `data/logs/`).

### Možnosť B — Spustenie zo zdrojových kódov (Python)

1. Nainštalujte [Python 3.13.17](https://www.python.org/)
2. Nainštalujte závislosti:

```powershell
pip install -r requirements.txt
```

3. *(Pre JXL a AVIF GainMap pri behu zo zdrojákov)* Umiestnite `cjxl.exe` (+ DLL) a `avifgainmaputil.exe` do priečinka `bin/` (alebo do systémového `PATH`).
4. Spustenie aplikácie a testov:

```powershell
# Grafické rozhranie (PySide6)
python src/main.py

# Príkazový riadok (CLI)
python src/main.py --cli --input ./photos --prefix "Foto" --quality-jpeg 95 --overwrite

# Automatizované testy
python -m pytest -v

# Zostavenie oboch Windows release balíkov (onefile EXE + portable ZIP)
python tools/build_exe.py
```

---

## Dokumentácia

- **[Používateľská príručka (SK)](./README-USER-SK.md)** · [English](./README-USER.md) · [Čeština](./README-USER-CZ.md)
- **[Vývojárska príručka (EN)](./README-DEVELOPER.md)** · **[Špecifikácia (EN)](./SPEC.md)** · **[Tech Stack (EN)](./TECH-STACK.md)**
- **[Agentický kontext (EN)](./README-AI-AGENT.md)** · **[Implementačný plán (SK)](./IMPLEMENTATION_PLAN.md)** · **[Audit (SK)](./AUDIT.md)** · **[Výskum (SK)](./RESEARCH.md)** · **[Changelog (SK)](./CHANGELOG.md)**
