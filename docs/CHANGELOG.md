# 📜 História zmien (`CHANGELOG.md`)

Všetky podstatné zmeny v projekte **TrueHDR Photo Converter** sa zaznamenávajú v tomto súbore.
Formát vychádza z [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) a projekt dodržiava [Sémantické verzovanie](https://semver.org/).

---

## [2026-11-23] — Premenovanie projektu na TrueHDR Photo Converter

**Súbory zmenené:**
- `src/gui.py`, `src/cli.py`, `src/config.py`, `tools/build_exe.py` – Zjednotenie názvu aplikácie na **TrueHDR Photo Converter** (titulok GUI okna), CLI `prog="TrueHDRPhotoConverter"`, `%APPDATA%/TrueHDRPhotoConverter/` a názvy release artefaktov `dist/TrueHDRPhotoConverter.exe` + `dist/TrueHDRPhotoConverter.zip`.
- `AGENTS.md`, `README.md`, `docs/*.md` – Aktualizácia všetkých názvov a referencií naprieč EN/SK/CZ dokumentáciou.

---

## [2026-11-23] — Odstránenie OpenCV (−112 MiB), upgrade balíkov a čistý portable ZIP

**Súbory zmenené:**
- `src/python_encoders.py`, `src/exr_encoder.py`, `tests/unit_tests.py`, `tests/test_retry_processing.py` – Úplne odstránená závislosť na `opencv-python` (`111,76 MiB` v builde); 8-bit aj 16-bit PNG sa dekódujú priamo cez `imagecodecs.png_decode` (`libpng 1.6.59`).
- `requirements.txt` – Aktualizované a zjednotené verzie: `PySide6==6.12.0`, `pytest==9.2.0`, `pytest-qt==4.5.0`, `pyinstaller==6.22.3`, `imagecodecs==2026.11.11`, `pillow==13.0.0`, `pillow-heif==1.8.1`, `OpenEXR==3.5.5`, `numpy==2.5.5` (bez `opencv-python`).
- `src/config.py`, `tools/build_exe.py` – Automatická detekcia prenosného režimu pri `--onedir` (`_internal/` vedľa EXE), takže do ZIPu netreba pribaliť `data/settings.json` (vytvorí sa automaticky z predvolených hodnôt); pridané `imagecodecs._png` do `HIDDEN_IMPORTS`, `--exclude-module cv2`, a automatické zmazanie rozbaleného `dist/TrueHDRConverter/` po vytvorení `dist/TrueHDRConverter.zip`.
- `AGENTS.md`, `docs/TECH-STACK.md`, `docs/README-DEVELOPER.md`, `docs/README-AI-AGENT.md` – Synchronizácia dokumentácie.

---

## [2026-11-23] — Prenosný `--onedir` + ZIP build, kompletná dokumentácia a príprava na publikovanie

**Súbory zmenené:**
- `tools/build_exe.py`, `src/config.py` – Rozšírený build skript o tvorbu oboch GitHub Release artefaktov jedným príkazom: samostatný `dist/TrueHDRConverter.exe` (`--onefile`) aj prenosný `dist/TrueHDRConverter/` (s priamym `bin/` a predvyplneným `data/settings.json` pre portable režim vrátane `data/logs/`) zabalený do `dist/TrueHDRConverter.zip`.
- `.gitignore`, `.gitattributes` – Doplnené ignorovanie Python/pytest/PyInstaller/build/`bin/`/`data/`/`logs/` artefaktov a explicitné `binary`/EOL pravidlá pre obrázky, EXE/DLL/ZIP a skripty.
- `AGENTS.md`, `README.md`, `docs/README-SK.md`, `docs/README-CZ.md`, `docs/README-USER.md`, `docs/README-USER-SK.md`, `docs/README-USER-CZ.md`, `docs/README-DEVELOPER.md`, `docs/README-AI-AGENT.md`, `docs/IMPLEMENTATION_PLAN.md` – Kompletná aktualizácia všetkých dokumentačných a jazykových mutácií (EN/SK/CZ) bez šablónových placeholderov.

---

## [2026-11-23] — Priečinok `bin/` (`avifgainmaputil` + `cjxl`) a self-contained PyInstaller `--onefile` build

**Súbory zmenené:**
- `bin/`, `.gitignore` – Vytvorený priečinok `bin/` (18,06 MiB, pridaný do `.gitignore`) s minimálnymi binárkami `avifgainmaputil.exe` (`12,36 MiB`, standalone) a `cjxl.exe` + jeho DLL knižnice (`5,70 MiB`).
- `src/models.py`, `src/converter.py`, `src/python_encoders.py` – Prepnutie JPEG XL na pribalený `cjxl` pre maximálnu kompresiu (`--gaborish 1 --brotli_effort 11 --modular 0`), pričom JPEG/UltraHDR JPEG/AVIF/HEIC/EXR ostávajú natívne v Pythone.
- `src/config.py` – `detect_tools()` uprednostňuje pribalený `bin/` (`_MEIPASS/bin` pre `--onefile`, `exe_dir/bin` pre `--onedir`, `root/bin` pre vývoj) na začiatku `PATH`.
- `tools/build_exe.py` – Aktualizovaný PyInstaller `--onefile` build tak, aby automaticky pribalil `bin/` + presné dynamické Cython moduly `imagecodecs`, `pillow_heif` a `OpenEXR` do jedného `dist/TrueHDRConverter.exe`.
- `tests/unit_tests.py`, `tests/test_retry_processing.py`, `docs/SPEC.md`, `docs/TECH-STACK.md` – Synchronizácia testov a dokumentácie.

---

## [2026-11-23] — 4:2:0 Ultra HDR JPEG Scenár 3 a viacvláknový AVIF/JXL v Python enkóderoch

**Súbory zmenené:**
- `src/python_encoders.py`, `src/converter.py` – Upravené `encode_hdr_gm_jpeg` na optimalizovaný 4:2:0 SDR JPEG základ so zachovaním ICC profilu (`jpeg8_encode` → `jpeg8_decode` → `ultrahdr_encode` → `ultrahdr_encode_jpeg`, pokles z `8,10 MiB` na `7,01 MiB`, `yuvj420p`), pridané plné viacvláknové spracovanie `numthreads=os.cpu_count()` pre AVIF aj JXL a `tilelog2=(2, 2)` pre `avif_encode` (~7,5× zrýchlenie AVIF).
- `docs/SPEC.md` – Zosynchronizovaná špecifikácia.

---

## [2026-11-23] — Prechod na natívne Python enkódery (`imagecodecs`, `pillow-heif`, `OpenEXR`)

**Súbory zmenené:**
- `src/python_encoders.py` – Nový natívny modul nahrádzajúci externé binárky (`cjpeg`, `cjxl`, `heif-enc`, `avifenc`, `ffmpeg`, `ultrahdr_app`) knižnicami `imagecodecs 2026.11.11` (`libjpeg-turbo 3.2.1`, `libjxl 0.13.0`, `libavif 1.4.2`/`aom 3.15.3`, `libultrahdr 2.0.2`), `pillow-heif 1.8.1` (`libheif 1.23.6` + `x265 4.3`) a `Pillow 13.0.0` + `numpy 2.5.5`. Každé PNG + ICC profil sa dekóduje do RAM iba raz (Unicode-safe cez `np.fromfile` + `cv2.imdecode`).
- `src/exr_encoder.py` – Pridaná funkcia `encode_hdr_rgb16_to_exr` na priame enkódovanie už načítaného `uint16` poľa z RAM bez opakovaného čítania PNG z disku.
- `src/converter.py`, `src/models.py`, `src/config.py` – Prepnutie celej SDR/HDR pipeline na natívne Python enkódery so zachovaným retry mechanizmom (max. 2 pokusy), čistením parciálnych výstupov, kooperatívnym zrušením a štruktúrovaným logovaním chýb; jediný voliteľný externý CLI nástroj ostáva `avifgainmaputil` pre `_HDR-GM.avif` (pričom aj jeho Scenario 0 fallback bez SDR PNG beží v Pythone bez `ffmpeg` a `ultrahdr_app`).
- `requirements.txt`, `tests/unit_tests.py`, `tests/test_retry_processing.py`, `docs/SPEC.md`, `docs/TECH-STACK.md`, `README.md`, `docs/README-SK.md` – Aktualizované závislosti, reálne binárne round-trip testy a dokumentácia.

---

## [2026-11-23] — EXR (HDR only) nezávislý od checkboxov HDR/PQ a HDR/GainMap

**Súbory zmenené:**
- `src/converter.py`, `src/worker.py` – Odstránené SDR EXR enkódovanie z `convert_sdr`; HDR EXR (`_HDR.exr`, lineárny 16-bit half-float Rec.2020) sa teraz generuje pri zapnutom `EXR (HDR only)` **nezávisle** od checkboxov `HDR/PQ` a `HDR/GainMap` (aj keď sú oba vypnuté).
- `src/gui.py` – Premenovanie checkboxu na **`EXR (HDR only)`** pri zachovaní presného spoločného zarovnania vstupných polí v sekciách `Settings` a `Codecs`.
- `tests/unit_tests.py`, `tests/test_gui_settings_persistence.py` – Overenie preskočenia EXR pre SDR, nezávislého generovania `_HDR.exr` pri vypnutých `HDR/PQ` aj `HDR/GainMap` a presného GUI zarovnania bez prekryvu.
- `docs/SPEC.md`, `README.md`, `docs/README-SK.md` – Synchronizácia dokumentácie.

---

## [2026-11-23] — Zjednotenie HDR HEIC spúšťania s JXL (zatiaľ bez GainMap)

**Súbory zmenené:**
- `src/converter.py` – Presunutie HDR HEIC enkódovania (`_HDR-PQ.heic`) do vetvy `any_hdr_enabled`, takže sa rovnako ako HDR JXL vygeneruje presne raz pri zapnutom aspoň jednom HDR checkboxe (`HDR/PQ` alebo `HDR/GainMap`), bez duplicity a pripravené na budúce rozdelenie na `_HDR-GM.heic` po pridaní `libultrahdr v2.x` / `libheif` `tmap` podpory.
- `tests/unit_tests.py` – Rozšírené overenie jednorazového behu `heif-enc` pri oboch HDR checkboxoch aj pri samotnom `HDR/GainMap`.
- `docs/SPEC.md`, `docs/RESEARCH.md`, `README.md`, `docs/README-SK.md` – Zosynchronizovaná dokumentácia pre HDR HEIC a budúci GainMap split.

---

## [2026-11-23] — Oprava SDR HEIC enkódovania pre libheif 1.23.4+

**Súbory zmenené:**
- `src/converter.py` – Odstránený flag `--bit-depth 8` z príkazu `heif-enc` v `convert_sdr`: `libheif 1.23.4` natívne enkóduje 8-bit PNG ako 8-bit HEIC a explicitné `--bit-depth 8` odmieta chybou (`exit code 5: Bit depth for input HDR images must be 9-16 bits.`).
- `tests/unit_tests.py` – Pridaný regresný test overujúci, že SDR `heif-enc` nepoužíva flag `--bit-depth`.
- `docs/SPEC.md` – Aktualizovaná špecifikácia SDR HEIC príkazu.

---

## [2026-11-23] — Zarovnanie Settings ↔ Codecs a checkbox Space after prefix

**Súbory zmenené:**
- `src/models.py`, `src/config.py`, `src/renamer.py`, `src/cli.py` – Pridaná voľba `space_after_prefix` (predvolene `True`, CLI `--no-space-after-prefix`), ktorá vkladá medzeru medzi prefix a počítadlo (napr. `Auto 23`), pokiaľ prefix už nekončí oddeľovačom (` `, `_`, `-`), a rešpektuje `counter_enabled`.
- `src/gui.py` – Pridaný checkbox **`Space after prefix`** priamo pod `Rename` a zjednotená šírka ľavého stĺpca `QGridLayout` medzi sekciami `Settings` a `Codecs`, aby boli všetky vstupné polia v jednej presnej vertikálnej rovine.
- `tests/test_gui_settings_persistence.py`, `tests/unit_tests.py` – Pridané testy pre `space_after_prefix` a geometrické overenie pixelovej roviny medzi `Settings` a `Codecs`.

---

## [2026-11-23] — EXR pre SDR aj HDR, default LJ2K, zoradenie kompresií a zarovnanie GUI

**Súbory zmenené:**
- `src/models.py` – Zmena predvolenej EXR kompresie na **`lj2k`**, preusporiadanie `EXR_COMPRESSIONS` (`none` → lossless od najhoršej po najlepšiu: `rle`, `htj2k32`, `htj2k256`, `pxr24`, `zstd`, `zips`, `zip`, `piz` → lossy od najhoršej po najlepšiu: `b44`, `b44a`, `dwaa`, `dwab`, `lj2k`).
- `src/exr_encoder.py`, `src/converter.py` – Pridaná podpora SDR EXR (`encode_sdr_png_to_exr`: sRGB EOTF LUT → lineárny 16-bit half-float, Rec.709 `chromaticities`, `whiteLuminance = 80.0`) v `convert_sdr`.
- `src/gui.py` – Premenovanie checkboxu na `EXR` (odstránené `(HDR Only)`), prepnutie sekcie `Codecs` na 12-stĺpcový `QGridLayout` pre presné zarovnanie `combo_exr_compression` ku spinboxom.
- `tests/unit_tests.py`, `tests/test_gui_settings_persistence.py` – Overenie defaultu `lj2k`, poradia kompresií, SDR EXR výstupu aj pixelového zarovnania widgetov v `Codecs`.

---

## [2026-11-23] — Natívny Python OpenEXR 3.5.5 enkóder (všetky kompresie + Rec.2020 chromaticities)

**Súbory zmenené:**
- `src/exr_encoder.py` – Nový natívny Python modul využívajúci oficiálny `OpenEXR==3.5.5`, `numpy` a `opencv-python`: rýchly 65536-prvkový SMPTE ST 2084 (PQ) EOTF LUT → lineárny 16-bit half-float (`whiteLuminance = 203.0`), explicitné Rec.2020 `chromaticities`, všetkých 14 OpenEXR kompresií (`piz`, `zip`, `zips`, `dwab`, `dwaa`, `lj2k`, `htj2k256`, `htj2k32`, `zstd`, `b44a`, `b44`, `pxr24`, `rle`, `none`) a funkcia `recompress_exr`.
- `src/models.py`, `src/config.py`, `src/gui.py`, `src/cli.py`, `src/converter.py` – Prepnutie `exr` kodeku z `ffmpeg` + `exrstdattr` na `openexr_python`, pridanie výberu kompresie `exr_compression` do `AppSettings`, GUI (`QComboBox` vedľa `EXR (HDR Only)`) aj CLI (`--exr-compression`).
- `requirements.txt` – Pridané `OpenEXR==3.5.5`, `numpy>=2.0.0`, `opencv-python>=4.10.0`.
- `tests/unit_tests.py`, `tests/test_gui_settings_persistence.py` – Overenie reálneho zápisu EXR hlavičky (`DWAB`, Rec.2020 `chromaticities`, `whiteLuminance = 203.0`) a GUI persistencie `exr_compression`.
- `README.md`, `docs/README-SK.md`, `docs/SPEC.md`, `docs/TECH-STACK.md` – Aktualizácia dokumentácie.

---

## [2026-11-23] — Pridanie EXR (HDR Only) cez FFmpeg a zjednotenie HDR JXL spúšťania

**Súbory zmenené:**
- `src/models.py`, `src/config.py`, `src/cli.py`, `src/gui.py` – Pridaný nový exportný kodek **`EXR (HDR Only)`** (`exr`) do sekcie `Codecs` (vyžaduje `ffmpeg`, bez lossy spinboxu, označený `16-bit half (ZIP16 lossless)`), oddelené `CODECS_WITH_QUALITY` od `ALL_CODECS`.
- `src/converter.py` – Implementované `_encode_hdr_exr` cez `ffmpeg` (`zscale` Rec.2020 PQ → Rec.2020 linear, `-format half -compression zip16`, suffix `_HDR.exr` + voliteľný Rec.2020 `chromaticities` tag cez `exrstdattr` ak je v `PATH`); upravené spúšťanie HDR JXL aj HDR EXR tak, aby sa vygenerovali presne raz pri zapnutom aspoň jednom HDR checkboxe (`HDR/PQ` alebo `HDR/GainMap`), JXL vždy ako `_HDR-PQ.jxl`.
- `tests/unit_tests.py`, `tests/test_gui_settings_persistence.py` – Overenie jednorazového behu JXL a EXR pri oboch HDR checkboxoch aj pri samotnom `HDR/GainMap`.
- `docs/SPEC.md`, `docs/RESEARCH.md`, `README.md`, `docs/README-SK.md` – Zaznamenaný benchmark EXR kompresií (`zip16` 63,30 MiB vs `piz` 64,47 MiB) a poznámka o budúcom rozšírení GainMap pre JXL.

---

## [2026-11-23] — Oddelenie HDR/PQ a HDR/GainMap, nová GUI sekcia a Rec.2020 Ultra HDR JPEG

**Súbory zmenené:**
- `src/models.py`, `src/config.py` – Rozdelenie HDR konfigurácie na `hdr_pq_enabled` a `hdr_gm_enabled` (so spätnou migráciou legacy `hdr_enabled`), detekcia nástrojov `ffmpeg`, `ultrahdr_app` a `avifgainmaputil`.
- `src/gui.py`, `src/cli.py` – Odstránenie starých checkboxov `Process SDR/HDR images` zo sekcie `Settings`, pridanie novej sekcie **`SDR/HDR processing`** pod `Codecs` s voľbami **`SDR`**, **`HDR/PQ`**, **`HDR/GainMap`**; CLI prepínače `--no-hdr-pq` a `--no-hdr-gm`.
- `src/converter.py`, `src/worker.py` – Nové výstupné suffixy **`_HDR-PQ`** a **`_HDR-GM`**, automatické párovanie HDR PNG so SDR PNG rovnakej bázy, implementácia Rec.2020 PQ Ultra HDR JPEG (`ultrahdr_app` Scenario 3 so SDR PNG a Scenario 0 s auto SDR odhadom bez SDR PNG) a ISO 21496-1 AVIF Gain Map (`avifgainmaputil combine`).
- `tests/unit_tests.py`, `tests/integration_test.py`, `tests/test_gui_settings_persistence.py` – Aktualizované a nové testy pre GUI persistenciu, `_HDR-PQ` / `_HDR-GM` suffixy, Scenario 3 aj Scenario 0.
- `README.md`, `docs/README-SK.md`, `docs/SPEC.md`, `docs/TECH-STACK.md`, `docs/RESEARCH.md` – Synchronizácia dokumentácie.

---

## [2026-11-23] — Komplexná oprava kodekov, living dokumentácie a pipeline

**Súbory zmenené:**
- `src/converter.py` – Oprava HDR HEIC transfer characteristic na 16 (PQ), odstránenie deštruktívneho `--ignore-icc`, úprava SDR AVIF CICP na `1/13/1`, explicitné vynútenie VarDCT (`--modular 0`) pre `cjxl`, prečistenie parametrov x265, použitie atomického `replace` pri publikovaní výstupov.
- `src/classifier.py` – Úplné odstránenie rizikového suffixu `-1`/`-2`, striktná podpora suffixov `_BW`, `_HDR`, `_BW_HDR` (SDR Color zostáva čisté bez prípony), zahrnutie EXR a JPG HDR do `unique_bases`.
- `src/worker.py` – Odstránenie pádu workeru pri absencii PNG (spracovanie aj pri prítomnosti samotných EXR / JPG HDR), nahradenie tichej výnimky korektným logovaním varovania.
- `src/config.py` – Rozšírenie povoleného rozsahu zerofill na 1 až 99 číslic, pridanie funkcie `logs_dir()` smerujúcej do `logs/` vo vývoji a `<config_root>/logs/` v release, automatická viditeľnosť štandardných ciest pre `cjxl` a ďalšie nástroje.
- `pytest.ini` – Konfigurácia lokálneho behu testov bez kolízií prístupových práv v `%LOCALAPPDATA%`.
- `tests/unit_tests.py` – Prispôsobenie testov novej schválenej schéme suffixov a pridanie testov pre zerofill do 99 a `logs_dir`.
- `README.md`, `docs/README-SK.md`, `docs/SPEC.md`, `docs/TECH-STACK.md`, `docs/README-DEVELOPER.md`, `docs/README-AI-AGENT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/RESEARCH.md` – Kompletne zmigrovaná živá dokumentácia z `.old` súborov do novej šablóny a zmazanie `README.md.old` a `README-SK.md.old`.
- `docs/AUDIT.md` – Vyčistenie vyriešených a overených položiek `AUD-001` až `AUD-010`.

**Vyriešené problémy z auditu:**
- ✅ **AUD-001 (P1):** Opravený `transfer_characteristic` v `heif-enc` z chybnej hodnoty 13 (sRGB) na **16** (SMPTE ST 2084 / PQ).
- ✅ **AUD-002 (P1):** Obnovená a zosúladená living dokumentácia vo všetkých určených jazykoch (EN/SK), zmazané staré `.old` súbory.
- ✅ **AUD-003 (P1):** Odstránený parameter `--ignore-icc` z AVIF konverzií pre plné zachovanie farebných profilov zo zdrojového PNG.
- ✅ **AUD-004 (P1):** Vyčistené nepodporované x265 parametre (`-p quality=...`) a potvrdený 10-bit YUV 4:2:0 formát pre AVIF a HEIC pre maximálnu úsporu dát a hardvérové dekódovanie cez NVENC.
- ✅ **AUD-005 (P2):** Opravený koeficient matice v SDR AVIF z BT.601 (`6`) na BT.709 (`1`) v `--cicp 1/13/1`.
- ✅ **AUD-006 (P2):** Zabezpečený plynulý beh workeru aj pri absencii PNG súborov a zahrnutie EXR/JPG HDR do `unique_bases`.
- ✅ **AUD-007 (P2):** Zrušená falošná detekcia čiernobieleho obrazu pri koncovke `-2`; nastavená striktná schéma bez prípony / `_BW` / `_HDR` / `_BW_HDR`.
- ✅ **AUD-008 (P2):** Vytvorený `pytest.ini` s izolovaným `basetemp` a `cache_dir` v projekte.
- ✅ **AUD-009 (P3):** Zjednotený rozsah zerofill na 1 až 99 číslic v GUI aj v konfiguračnej vrstve.
- ✅ **AUD-010 (P3):** Zavedený `logs_dir()` smerujúci do `logs/` vo vývojovom režime a odstránené tiché potláčanie výnimiek v `_rename_companion_files`.

**Overené:**
- `python -m pytest` – všetkých 42 automatických testov prešlo za 0.28s.
- `ffprobe` na vygenerovanom HEIC z `temp/Audi A7 82_HDR.png` potvrdil `Color transfer: smpte2084`, `Color primaries: bt2020`, `Pix fmt: yuv420p10le`.
- Overené nové verzie externých nástrojov: FFmpeg 9.1, libjxl 0.13.0, libjpeg-turbo 3.2.1, libheif 1.23.4, libavif 1.4.2.
