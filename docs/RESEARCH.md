# 🔬 Technický výskum a rozhodnutia (`RESEARCH.md`)

Zdroje, technické overenia a kľúčové rozhodnutia projektu **TrueHDR Photo Converter**.

---

## 1. HDR formáty a porovnanie s Lightroom Classic (`2026-11-23`)

- **Zistenia z analýzy vzoriek v `temp/`:**
  - **AVIF HDR:** Lightroom exportuje 10-bit YUV 4:4:4 (`yuv444p10le`), BT.2020 primaries, SMPTE ST 2084 (PQ) transfer a BT.2020 non-constant matrix (CICP `9/16/9`).
  - **HEIC HDR:** Vyžaduje HEVC Main 10 profil, 10-bit hĺbku, Primaries 9 (Rec.2020), Transfer 16 (PQ) a Matrix 9. Nastavenie Transfer 13 v predchádzajúcom kóde spôsobovalo nesprávne zobrazenie sRGB gama krivky.
  - **Subsampling 4:2:0 vs. 4:4:4:** Používateľ potvrdil voľbu **4:2:0 10-bit** pre AVIF a HEIC z dôvodu výraznej úspory dát a hardvérovej podpory dekódovania na moderných GPU (NVIDIA NVENC/NVDEC).
  - **JPEG HDR (Ultra HDR / ISO 21496-1):** Lightroom exportuje MPF (Multi-Picture Format) obsahujúci primárny 8-bit SDR JPEG obraz a sekundárny 8-bit Gain Map JPEG obraz.
  - **EXR:** 16-bit/32-bit float formát. FFmpeg 9.1 v systémovom PATH priamo podporuje konverziu 16-bit HDR PNG do EXR (`-c:v exr -pix_fmt gbrpf16le` / `gbrpf32le`).

## 2. JPEG XL enkódovanie (VarDCT vs. Modular) a iPhone JXL HDR

- **Zistenia:**
  - `cjxl 0.13.0` podporuje VarDCT (`--modular 0`, predvolené pre lossy) aj Modular (`--modular 1`, bezstratové / palety). Pri `--quality 100` a `--modular 0` `cjxl` bezpečne prepne na Modular lossless.
  - Vo VarDCT režime `cjxl` interne prevádza vstup do psychovizuálneho priestoru **XYB**, ktorý zachováva farebné vnímanie ľudského oka s maximálnou kompresiou. Do hlavičky kontajnera JXL ukladá cieľový profil (Rec.2100 PQ).
  - **Apple iPhone & JXL:** Od iPhone 16 Pro / iOS 18+ Apple používa **JPEG XL (Lossless aj Lossy)** ako vnútornú kompresiu pre **Apple ProRAW (DNG 1.7)** vrátane plného HDR rozsahu, a na úrovni OS (iOS 18/19/26, macOS, Safari/WebKit) poskytuje natívne systémové dekódovanie aj zápis JXL (vrátane HDR). Pre bežné fotky z fotoaparátu však primárne zostáva HEIF/HEIC s Gain Mapou.

## 3. ISO 21496-1 Gain Map (Ultra HDR v2, AVIF, HEIC) vs. Klasické HDR PQ (`2026-11-23`)

- **Zistenia:**
  - Štandard **ISO/IEC 21496-1** zjednocuje HDR Gain Map metadáta naprieč **JPEG (Ultra HDR)**, **HEIC/HEIF** (`libheif 1.23+` `tmap`) aj **AVIF** (`libavif 1.4+` / `avifgainmaputil`, `libultrahdr 2.0+`).
  - **Klasické HDR PQ (10-bit single-layer):** Jeden stream v PQ/BT.2020. Menšia veľkosť (nie je druhá vrstva), priamy 10-bit HW decode na GPU (NVDEC), výborné na archiváciu a HDR-only fotogalérie; ale horší fallback na SDR obrazovkách (závisí od tone-mappingu prehliadača/OS).
  - **Gain Map HDR (ISO 21496-1: SDR base + Gain Map):** Dve vrstvy (8-bit SDR základ + nízko-rozlíšená/komprimovaná gain mapa). O ~20–50 % väčší súbor než SDR, mierne vyššia réžia pri enkódovaní/dekódovaní (2 dekódovania + GPU/CPU shader kompozícia), ale **100 % spätná kompatibilita** s akýmkoľvek SDR displejom a dynamické prispôsobenie presnému HDR headroomu displeja. Do budúcnosti sa pre web, mobily a zdieľanie stáva hlavným štandardom Gain Map (ISO 21496-1), zatiaľ čo 10/16-bit PQ zostáva dôležité ako master/archív a pre video/NVDEC workflowy.

## 4. OpenEXR vzorka z Photoshopu (`Audi A7 40_HDR.exr`) a benchmark FFmpeg kompresií (`2026-11-23`)

- **Overenie Photoshop EXR cez `exrheader` / `exrinfo` (OpenEXR 3.5.4):**
  - Formát: OpenEXR verzia 2, `scanlineimage`, 3852 × 4815, 3 kanály (`R`, `G`, `B`) v **16-bit half-float**, kompresia **PIZ** (bezstratová wavelet kompresia v blokoch po 32 scanlines), lineárna prenosová krivka.
- **Benchmark 16-bit half-float EXR kompresií (oficiálny OpenEXR 3.5.4 `exrmetrics -z all`) vs. moderné kodeky na `Audi A7 82_HDR.png` (6000 × 4000 = 24 MPx, vstupný 16-bit PNG = 70,21 MiB / 24,54 bpp):**
  - *EXR Bezstratové (Lossless):* `piz` **60,17 MiB** (21,03 bpp, najmenší lossless EXR), FFmpeg `zip16` **63,30 MiB** (22,12 bpp, najmenší v samotnom FFmpeg a rýchle čítanie 0,24 s), OpenEXR `zip` **64,47 MiB** (22,53 bpp), `zips` **66,18 MiB**, `zstd` **68,23 MiB**, `htj2k256` **70,61 MiB**, `rle` **103,05 MiB**, `none` **137,39 MiB** (48,02 bpp).
  - *EXR Stratové (Lossy):* `lj2k` (lossy HTJ2K, OpenEXR 3.5) **10,95 MiB** (3,83 bpp), `dwab` (DCT 256-line, def=45) **13,85 MiB** (4,84 bpp), `dwaa` (DCT 32-line, def=45) **14,10 MiB** (4,93 bpp), `b44a` **58,07 MiB** (20,30 bpp).
  - *Porovnanie s HDR foto kodekmi (tá istá 24 MPx fotka):* JXL `q=100` lossless **45,91 MiB** (16,05 bpp), HEIC PQ `q=90` **6,07 MiB** (2,12 bpp), Ultra HDR JPEG `q=90` **4,89 MiB** (1,71 bpp), AVIF PQ `q=90` **2,11 MiB** (0,74 bpp), JXL VarDCT `q=90` **1,43 MiB** (0,50 bpp).
- **Farebný priestor a transfer EXR:**
  - OpenEXR je čisto **lineárny floating-point** formát (nemá PQ krivku ani GainMap). Pri prevode z 16-bit Rec.2020 PQ PNG je nevyhnutné použiť `zscale=pin=bt2020:tin=smpte2084:min=gbr:rin=full:p=bt2020:t=linear:m=gbr:r=full` na presnú EOTF linearizáciu pri zachovaní Rec.2020 gamutu.
  - Atribút `chromaticities` pre Rec.2020 (`0.708 0.292 0.170 0.797 0.131 0.046 0.3127 0.3290`) FFmpeg sám nezapisuje; ak je na `PATH` prítomný oficiálny `exrstdattr`, aplikácia ho voliteľne doplní do EXR hlavičky.
- **Poznámka k budúcemu JXL a HEIC GainMap:**
  - Keďže `cjxl 0.13.0` ani nainštalovaný `heif-enc` (`libheif 1.23.4`, bez experimentálneho PR #1503 `tmap` API) a `ultrahdr_app 1.5.1` zatiaľ nemajú stabilnú Windows CLI podporu pre ISO 21496-1 Gain Map, HDR JXL aj HDR HEIC sa zatiaľ vždy generujú iba raz ako `_HDR-PQ.jxl` / `_HDR-PQ.heic`, ak je zapnutý aspoň jeden z HDR checkboxov (`HDR/PQ` alebo `HDR/GainMap`). Po pridaní podpory (`libultrahdr v2.x` / `libheif` `tmap` pre HEIC a budúce `cjxl` pre JXL) sa toto správanie jednoducho rozdelí na samostatné `_HDR-PQ` a `_HDR-GM` výstupy rovnako ako pri AVIF.

## 5. Zdroje a špecifikácie

- [libjpeg-turbo](https://github.com/libjpeg-turbo/libjpeg-turbo) v3.2.1
- [libjxl](https://github.com/libjxl/libjxl) v0.13.0
- [libheif](https://github.com/strukturag/libheif) v1.23.4
- [libavif](https://github.com/AOMediaCodec/libavif) v1.4.2
- [libultrahdr](https://github.com/google/libultrahdr) v1.5.1 (MSYS2 CLI) / v2.0.2 (upstream)
- [OpenEXR](https://github.com/AcademySoftwareFoundation/openexr) v3.5.4 / v3.5.5
- [ITU-T H.273 / ISO 23091-2](https://www.itu.int/rec/T-REC-H.273) – Kódy CICP pre Primaries, Transfer a Matrix
- ISO/IEC 21496-1 – Gain map metadata for image conversion
