# 📖 Používateľská príručka (`README-USER-SK.md`)

[English](./README-USER.md) | **Slovenčina** | [Čeština](./README-USER-CZ.md)

Tento návod je určený pre koncového používateľa aplikácie **TrueHDR Photo Converter**.

---

## 1. O aplikácii

- Automaticky roztriedi, premenuje a skonvertuje exportované SDR (8-bit sRGB) a True HDR (16-bit Rec.2020 PQ) fotografie (PNG, EXR, HDR JPEG) do moderných formátov: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL**, **HEIC**, **AVIF (PQ & Gain Map)** a **OpenEXR (HDR)**.
- Nikdy neprepisuje pôvodné fotky – všetky výsledky bezpečne ukladá do podpriečinka `output/` vo vybranom adresári.

---

## 2. Požiadavky a inštalácia

- **Operačný systém:** Windows 10 / Windows 11 (64-bit)
- **Ďalšie požiadavky:** Žiadne pri použití hotových balíkov z GitHub Releases.

### Výber verzie na stiahnutie

1. **Jediný EXE súbor (`TrueHDRPhotoConverter.exe`):**
   - Stačí stiahnuť a spustiť `TrueHDRPhotoConverter.exe` (prvý štart trvá ~3 s kvôli rozbaleniu).
   - Nastavenia a logy sa ukladajú do `%APPDATA%\TrueHDRPhotoConverter\`.
2. **Prenosná verzia (`TrueHDRPhotoConverter.zip`):**
   - Rozbaľte priečinok `TrueHDRPhotoConverter/` kamkoľvek (na disk, USB kľúč a pod.) a spustite `TrueHDRPhotoConverter.exe`.
   - Okamžitý štart (`<1 s`), 100 % prenosné – nastavenia (`data/settings.json`) aj logy (`data/logs/`) ostávajú priamo v rozbalenom priečinku.

---

## 3. Ovládanie a prvé kroky

1. **Výber priečinka:** Kliknite na **Select image directory** a vyberte priečinok s vašimi exportovanými PNG/EXR/HDR JPG súbormi.
2. **Nastavenia (`Settings`):**
   - **Rename:** Zapne/vypne premenovanie a určí prefix (predvolene `Image`).
   - **Add space:** Automaticky vloží medzeru medzi prefix a číslo (napr. `Dovolenka 01`), ak prefix už nekončí medzerou, `_` alebo `-`.
   - **Counter & Zerofill:** Počiatočné číslo a automatické/manuálne doplnenie núl (1–99 číslic).
3. **Výber kodekov (`Codecs`):**
   - Zaškrtnite želané formáty **JPEG**, **JPEG XL**, **HEIC**, **AVIF** (kvalita 0–100) a **EXR (HDR only)** (výber kompresie, predvolená `LJ2K (Lossy HTJ2K)`).
4. **Režim spracovania (`SDR/HDR processing`):**
   - **SDR:** Spracuje bežné 8-bit SDR PNG fotky.
   - **HDR/PQ:** Vytvorí 10/16-bit Rec.2020 PQ výstupy (`_HDR-PQ.jxl`, `_HDR-PQ.heic`, `_HDR-PQ.avif`).
   - **HDR/GainMap:** Vytvorí ISO 21496-1 Gain Map výstupy (`_HDR-GM.jpg`, `_HDR-GM.avif`) z párového SDR + HDR PNG (alebo automatickým SDR fallbackom, ak SDR PNG chýba).
   - *Poznámka:* `EXR (HDR only)` vytvára lineárny Rec.2020 `_HDR.exr` nezávisle od checkboxov `HDR/PQ` a `HDR/GainMap`.
5. **Spustenie:** Kliknite na **Process images** (bežiace spracovanie možno kedykoľvek zastaviť tlačidlom **Stop**). Po dokončení sa zobrazí súhrnný dialóg.

---

## 4. Riešenie bežných problémov (FAQ)

- **Upozornenie Windows SmartScreen pri prvom spustení:** EXE nie je digitálne podpísané plateným certifikátom – kliknite na **Ďalšie informácie → Napriek tomu spustiť** (prípadne použite prenosný ZIP).
- **Kde nájdem skonvertované súbory?** V podpriečinku `<vybraný priečinok>\output\` spolu s `logging.log`, `rename.log` a `errors.log`.
- **Pri jednej fotke zlyhal konkrétny kodek:** Aplikácia krok raz zopakuje a plynulo pokračuje ostatnými kodekmi a fotkami; detail chyby nájdete v `output\errors.log`.
