# Crawlee-Python — Qualitative Evaluation
**Datum:** 2026-06-22
**Kontext:** Marcus will wissen, ob Crawlee den bestehenden RSS-basierten Research-Workflow verbessern kann.

---

## Smoke-Test Ergebnisse

Getestet mit `BeautifulSoupCrawler` (HTTP, kein Headless Browser) aus Crawlee 1.7.2, Python 3.12, `/tmp`-Sandbox.

### Test 1: netzpolitik.org (haben wir per RSS)

| Aspekt | RSS (blogwatcher) | Crawlee (BeautifulSoupCrawler) |
|--------|-------------------|-------------------------------|
| **Output** | Titel + ~200 Zeichen Summary | Vollständiger Artikeltext, Autor, Datum, Kategorie, Verwandte Begriffe |
| **Text-Qualität** | Gut für Scannen | Hervorragend für Tiefen-Recherche |
| **Performance** | <1s pro Feed | ~2.7s pro Request |
| **Zuverlässigkeit** | Sehr hoch | Hoch (0 Fehler im Test) |
| **Link-Discovery** | Nur Feed-URLs | Automatisch Archivseiten + Artikel-Links |
| **Datengröße** | ~500 bytes/Artikel | ~5-15KB/Artikel (10-30× mehr) |

**Beispiel Crawlee-Output** (Tag-Archiv-Seite "Databroker Files"):
```
Databroker-Deals der Polizei: Opposition fordert Aufklärung in acht Bundesländern
Angeblich nur zu Werbezwecken erhobene Handy-Standortdaten dürften ein verlockendes 
Angebot für Ermittler*innen sein (Symbolbild).
von Sebastian Meineck, 9. Juni 2026
[voller Artikeltext mit 7+ KW-Einträgen, Verwandte Begriffe, Tags]
```

### Test 2: kontrapolis.info (kein RSS in unserem Set)

| Aspekt | Ergebnis |
|--------|----------|
| **Erreichbarkeit** | ✅ HTTP 200 (WordPress) |
| **Crawlee-Erfolg** | ❌ SSL-Zertifikatsfehler (Crawlee bricht ab, curl -k funktioniert) |
| **Content-Struktur** | Artikel archiviert unter `/beitrag/YYYY/`, klar erkennbar |
| **Typ** | WordPress, keine JS nötig, Crawle-bar |

**Problem:** Crawlee lehnt SSL-Verbindung ab → konfigurierbar, aber separater Aufwand.

### Test 3: c-base.org

| Aspekt | Ergebnis |
|--------|----------|
| **Erreichbarkeit** | ✅ HTTP 200 |
| **Crawlee-Erfolg** | Teilweise — Hauptseite erreichbar, aber JS-heavy SPA → keine Artikel-Links gefunden |
| **Braucht Playwright?** | Wahrscheinlich ja |

---

## Qualitative Bewertung

### Wann ist RSS besser (blogwatcher)?

- **Monitoring/Scanning:** Täglicher Überblick über 6+ Feeds
- **Ressourcen:** Minimaler Footprint (~500 bytes/Artikel)
- **Zuverlässigkeit:** RSS ist ein Protokoll — Änderungen an Websites brechen RSS selten
- **Noise/Signal:** RSS-Feeds enthalten nur das, was Herausgeber teilen wollen — weniger Noise
- **Datenschutz:** Kein Kontakt mit Website-Tracking (kein User-Agent-Fingerprint nötig)

### Wann ist Crawlee besser?

- **Volltext-Tiefenrecherche:** Artikel komplett lesen, nicht nur Summary
- **Quellen ohne RSS:** Viele relevante Sites haben keinen Feed (z.B. manche Blogs, Foren, Substack-Artikel hinter Paywalls)
- **Archiv-Erschließung:** Tag-/Kategorie-Seiten crawlen für thematische Bestände
- **Anti-Bot-Umgehungen:** Proxy-Rotation, Fingerprinting bei blockierten Quellen
- **Strukturierte Extraktion:** JSON-LD, Microdata, Schema.org — für RAG-Pipeline
- **Multi-Step-Pipelines:** Detailseite crawlen → in Datenbank → für LLM-Kontext

### Trade-off zusammen

```
RSS:          Monitoring  ←————→  Tiefenrecherche :Crawlee
Niedrig       Komplexität  ————————→            Hoch
Schnell       Ressourcen  ————————→            Schwer
Zuverlässig   Datenmenge   ————————→            Umfangreich
```

---

## Empfehlung

### Für den Daily-Research-Workflow:

**RSS bleibt Primary** (blogwatcher):
- 6 Feeds, täglich ~5:30 UTC, 301 ungelesene Artikel
- Hervorragend für Jacobin, LabourNet, Netzpolitik, AI Now, Real Life, Rest of World
- Kein Wartungsaufwand, stabil, low-footprint

**Crawlee als punktuelles Research-Tool** (nicht als Cron-Integration):
- Wenn ein Thema Tiefenrecherche braucht: Crawlee-Script laufen lassen
- Quellen die wir nicht per RSS abdecken (z.B. kontrapolis.info, eigene Archiv-Suche)
- Konfigurationsaufwand: ~30 Min pro Quelle (SSL, Selector-CSS, Output-Format)

### Konkreter Vorschlag

1. **kontrapolis.info** als erste Nicht-RSS-Quelle: SSL-Problem in Crawlee fixen, 1-Page-Test
2. **Volltext-Crawl für spezifische Tag-Seiten** (z.B. netzpolitik.org/tag/datenschutz) → wenn wir einen Topic tiefer recherchieren wollen
3. **NICHT:** Crawlee als Ersatz für blogwatcher im Daily-Cron — dafür ist RSS zu gut

### Setup wenn umgesetzt

```bash
# Datenverzeichnis (wie besprochen)
mkdir -p data/crawler/

# Minimal-Setup (BeautifulSoupCrawler, SQLite-Storage)
pip install 'crawlee[beautifulsoup,sql_sqlite]'

# Optional: SSL-Verifikation abschalten für kontrapolis etc.
# (in ProxyConfiguration oder HTTPClient-Konfiguration)
```

---

## Offene Frage an Marcus

Soll ich:
- **A)** kontrapolis.info als erste Nicht-RSS-Quelle einrichten (SSL-Fix + Crawl-Script in `data/crawler/`)
- **B)** Erstmal RSS-Pipeline abschließen und Crawlee für später aufheben
- **C)** Crawlee für eine spezifische Recherche-Hypothese testen (z.B. "Crawle alle Artikel zum Thema Überwachung der letzten 6 Monate")

**Priorität:** RSS (blogwatcher) jetzt nicht anfassen — Crawlee nur als Ergänzung für spezifische Recherche-Zwecke.
