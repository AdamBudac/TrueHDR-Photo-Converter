# 📖 Uživatelská příručka (`README-USER-CZ.md`)

[English](./README-USER.md) | [Slovenčina](./README-USER-SK.md) | **Čeština**

Tento návod je určen pro koncového uživatele aplikace **TrueHDR Photo Converter**.

---

## 1. O aplikaci

- Automaticky roztřídí, přejmenuje a zkonvertuje exportované SDR (8-bit sRGB) a True HDR (16-bit Rec.2020 PQ) fotografie (PNG, EXR, HDR JPEG) do moderních formátů: **JPEG**, **Ultra HDR JPEG (Gain Map)**, **JPEG XL**, **HEIC**, **AVIF (PQ & Gain Map)** a **OpenEXR (HDR)**.
- Nikdy nepřepisuje původní soubory – všechny výstupy bezpečně ukládá do podsložky `output/` ve vybraném adresáři.

---

## 2. Požadavky a instalace

- **Operační systém:** Windows 10 / Windows 11 (64-bit)
- **Další požadavky:** Žádné při použití hotových balíků z GitHub Releases.

### Výběr verze ke stažení

1. **Jediný EXE soubor (`TrueHDRPhotoConverter.exe`):**
   - Stačí stáhnout a spustit `TrueHDRPhotoConverter.exe` (start trvá ~3 s kvůli rozbalení).
   - Nastavení a logy se ukládají do `%APPDATA%\TrueHDRPhotoConverter\`.
2. **Přenosná verze (`TrueHDRPhotoConverter.zip`):**
   - Rozbalte složku `TrueHDRPhotoConverter/` kamkoli (na disk, USB flash disk apod.) a spusťte `TrueHDRPhotoConverter.exe`.
   - Okamžitý start (`<1 s`), 100 % přenosné – nastavení (`data/settings.json`) i logy (`data/logs/`) zůstávají uvnitř rozbalené složky.

---

## 3. Ovládání a první kroky

1. **Výběr složky:** Klikněte na **Select image directory** a vyberte složku s exportovanými PNG/EXR/HDR JPG soubory.
2. **Nastavení (`Settings`):**
   - **Rename:** Zapne/vypne přejmenování a nastaví prefix (výchozí `Image`).
   - **Add space:** Automaticky vloží mezeru mezi prefix a číslo (např. `Dovolena 01`), pokud prefix již nekončí mezerou, `_` nebo `-`.
   - **Counter & Zerofill:** Počáteční číslo a automatické/manuální doplnění nul (1–99 číslic).
3. **Výběr kodeků (`Codecs`):**
   - Zaškrtněte požadované formáty **JPEG**, **JPEG XL**, **HEIC**, **AVIF** (kvalita 0–100) a **EXR (HDR only)** (výběr komprese, výchozí `LJ2K (Lossy HTJ2K)`).
4. **Režim zpracování (`SDR/HDR processing`):**
   - **SDR:** Zpracuje běžné 8-bit SDR PNG fotky.
   - **HDR/PQ:** Vytvoří 10/16-bit Rec.2020 PQ výstupy (`_HDR-PQ.jxl`, `_HDR-PQ.heic`, `_HDR-PQ.avif`).
   - **HDR/GainMap:** Vytvoří ISO 21496-1 Gain Map výstupy (`_HDR-GM.jpg`, `_HDR-GM.avif`) z párového SDR + HDR PNG (nebo automatickým SDR fallbackem, pokud SDR PNG chybí).
   - *Poznámka:* `EXR (HDR only)` vytváří lineární Rec.2020 `_HDR.exr` nezávisle na přepínačích `HDR/PQ` a `HDR/GainMap`.
5. **Spuštění:** Klikněte na **Process images** (zpracování lze kdykoli ukončit tlačítkem **Stop**). Po dokončení se zobrazí souhrnný dialog.

---

## 4. Řešení běžných problémů (FAQ)

- **Upozornění Windows SmartScreen při prvním spuštění:** EXE není digitálně podepsáno placeným certifikátem – klikněte na **Další informace → Přesto spustit** (případně použijte přenosný ZIP).
- **Kde najdu zkonvertované soubory?** V podsložce `<vybraná složka>\output\` společně s `logging.log`, `rename.log` a `errors.log`.
- **U jedné fotky selhal konkrétní kodek:** Aplikace krok jednou zopakuje a plynule pokračuje ostatními kodeky a fotkami; detail chyby je v `output\errors.log`.
