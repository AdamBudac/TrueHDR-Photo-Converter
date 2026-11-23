---
name: changelog-entry
description: Write a consistent, evidence-backed entry in docs/CHANGELOG.md after completing a logical code, config, or documentation change. Use at the end of a task before handing results back to the user.
---

# Changelog Entry Procedure

1. Open `docs/CHANGELOG.md` and add a single cohesive entry per logical change at the top (under the current unreleased heading or dated release section) in **Slovak**.
2. Use the standard structure:
   ```markdown
   ### [YYYY-MM-DD] Stručný názov zmeny

   **Súbory zmenené:**
   - `path/to/file` – stručný popis zmeny

   **Detaily:**
   - ✅ Added / Changed / Fixed / Removed (vrátane `AUD-XXX` ID, ak ide o opravu z auditu)
   - ⚠️ Otvorené poznámky alebo vedomé obmedzenia (ak existujú)

   **Postup overenia:**
   - Ako zmenu reprodukovateľne overiť

   **Overené:**
   - Skutočne vykonané príkazy, počty prešlých testov a výsledok (alebo jasný dôvod, prečo sa runtime test nespúšťal, napr. čisto dokumentačná úprava)
   ```
3. Verification honesty check:
   - Never list planned checks under **Overené**.
   - Never claim runtime verification if only static checks or compilation ran.
   - Never include secrets, tokens, or real credentials in changelog notes.
