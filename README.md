# fitness nation | Katalog-Showroom

Alternative Katalog-Ansicht (eigenes Projekt neben `fn-webkatalog`):
**fester nummerierter Produkt-Index links** (Preise, Filter Software/Hardware) +
**volle Produkt-Spreads rechts** (Bildbühne + Datenblatt-Spec-Grid).
Recherche-Basis: Galerie-Zurückhaltung der Luxus-Kataloge × Spec-Dokumentation à la Teenage Engineering.

## Betrieb
- Inhalte: `content/<katalog>/<sprache>.json` (Kopie der Quelle aus fn-webkatalog)
- Preise: live aus `_WISSENSDATENBANK/FN_HARDWARE_MASTERDATA.json` + `FN_MASTERDATA.json` beim Build
- Bauen: `python3 build/build.py` → `site/de`, `site/en`, `site/de/smart`, `site/en/smart`
- Deploy: push → Vercel (Output Directory `site`, kein Build-Command)

Präsentationsmodus: Taste **F** (Pfeile/Clicker, `.` = Blackout, Esc = Ende).
