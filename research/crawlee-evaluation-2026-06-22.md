# Crawlee-Python — Qualitative Evaluation (Phase 2: Mehr Quellen)
**Aktualisiert:** 2026-06-22 11:15
**Test-Quellen:** netzpolitik.org, heise.de, telepolis.de, golem.de, taz.de, akweb.de, kontrapolis.info

---

## Smoke-Test Ergebnisse

Getestet mit `BeautifulSoupCrawler` (HTTP, kein Headless Browser) aus Crawlee 1.7.2, Python 3.12.

| Quelle | Crawlee-Status | Text-Länge | Artikel-Links | Paywall? | RSS vorhanden? | RSS vs Crawlee |
|--------|---------------|-----------|---------------|----------|---------------|----------------|
| **heise.de** | ✅ Volltext | ~33KB/Seite | 6 | Nein | ✅ Ja (Atom/RDF) | RSS: ~170 Zeichen. Crawlee: ganzer Artikel. **Klasse 1** |
| **netzpolitik.org** | ✅ Volltext | ~5-15KB/Artikel | 38-40 | Nein | ✅ Ja | RSS: ~200 Zeichen. Crawlee: Autor+Datum+Tags+Volltext. **Klasse 1** |
| **taz.de** | ✅ Volltext | ~33KB/Seite | 3 | Nein (aber taz-zahl-ich) | ✅ Ja | RSS: Snippets. Crawlee: ganzer Text. **Klasse 1** |
| **telepolis.de** | ✅ Erreichbar | ~7KB/Seite | 1 | Nein | ❌ jetzt bei heise | Jetzt heise+Telepolis-Integration. Braucht anderen Crawl-Ansatz. **Klasse 2** |
| **akweb.de** (ak – analyse & kritik) | ✅ Volltext | ~10KB/Seite | 0 (Heuristik) | Nein | ✅ RSS vorhanden | WordPress. Artikel-URLs in Ausgabe sichtbar aber Crawlee-Linksuche findet sie nicht. **Klasse 2** |
| **kontrapolis.info** | ⚠️ SSL-Fehler | — | — | Nein | ❌ Kein RSS | Crawlee bricht ab, curl -k funktioniert. **Fixbar (~15 Min)** |
| **golem.de** | ❌ Blockiert | ~2.8KB | 0 | **JA (Cookie-Wall)** | ✅ Ja (Feed) | Paywall blockiert BeautifulSoupCrawler komplett. RSS existiert aber ist Paid-only. **Nicht machbar** |
| **c-base.org** | ⚠️ SPA | — | — | Nein | ❌ Kein RSS | Braucht PlaywrightCrawler (Browser). **Klasse 3** |

---

## RSS vs Crawlee — Qualitativer Vergleich

**RSS (blogwatcher) — Stärken:**
- Zuverlässig, protokollbasiert, nie blockiert
- ~500 bytes/Artikel, geringer Footprint
- Für Jacobin, LabourNet, Netzpolitik, AI Now, Real Life, Rest of World: ausreichend
- Maintenance: praktisch null

**Crawlee (BeautifulSoupCrawler) — Stärken:**
- Volltext. Bei heise/taz/netzpolitik: 10-50× mehr Text als RSS
- Strukturierte Daten: Autor, Datum, Tags, verwandte Begriffe
- Link-Discovery: crawlt automatisch Archiv-/Tag-Seiten
- Quellen ohne RSS: erreichbar wenn kein Paywall/SSL

---

## Was heißt das für uns konkret?

**Quellen die Crawlee wirklich besser macht:**

→ **heise.de:** 33KB Volltext vs 170 Zeichen RSS-Snippet. Für Tech/IT-Nachrichten die wir verstehen wollen (KI, Digitalisierung, Plattformökonomie) ist der Volltext Gold wert. Aber: heise ist nicht unser Primary-Fokus (wir wollen linke/politische Perspektive, nicht Tech-Per se).

→ **netzpolitik.org:** Schon im RSS-Set, aber Crawlee gibt Volltext. Wenn wir tiefer recherchieren wollen: Crawlee. Für Daily-Monitoring: RSS reicht.

→ **taz.de:** Ähnlich wie heise — taz hat aber ein Paywall-Modell (taz-zahl-ich). Crawlee-Volltext auf der Startseite funktioniert, aber Artikel hinter Paywall möglicherweise nicht.

**Quellen die ich NICHT empfehlen würde:**
- **golem.de:** Paywall. Kein Crawling ohne Browser (Playwright). Auch RSS ist Paid-only.
- **c-base.org:** Braucht PlaywrightCrawler. Für die paar Space-News nicht den Aufwand wert.

**Quellen die einen Versuch wert sind:**
- **kontrapolis.info:** SSL-Fix in Crawlee (~15 Min). Linke Berliner Zeitung, kein RSS, WordPress → crawlabar.
- **telepolis.de:** Jetzt heise+Telepolis-Integration → andere Crawl-Strategie nötig (Telepolis-Artikel haben alte URLs, werden auf heise umgeleitet).

---

## Empfehlung

### Setup das ich vorschlage:

```
data/crawler/
├── README.md
├── crawlee_sqlite_test.py    # Smoke-Test Script
├── kontrapolis_crawl.py       # Erste Nicht-RSS-Quelle
└── output/                    # Crawlee SQLite Storage
```

**Nicht** als Daily-Cron — RSS bleibt Primary. Aber als Tool das wir nutzen wenn wir ein Thema tiefer recherchieren.

### Warum nicht als Cron-Integration:

1. **Mehr Rauschen als Nutzen im Daily-Context** — Volltext von heise/taz sind 33KB/Artikel. Das sind keine Monitoring-Daten mehr, das sind Recherche-Daten.
2. **Crawlzeit** — 25 Requests auf heise brauchen ~1:17min. Im Cron-Context zu viel.
3. **RSS ist für Monitoring gebaut** — Die 6 bestehenden Feeds delivern 301 Artikel/Tag die wir schon kaum schaffen.

### Wann Crawlee statt RSS:

- Wenn wir eine **spezifische Recherche** haben ("Was hat netzpolitik.org in den letzten 3 Monaten zum Thema Datenschutz geschrieben?")
- Wenn wir eine **Quelle ohne RSS** erschließen wollen (kontrapolis.info)
- Wenn wir **Volltext für eine RAG-Pipeline** brauchen (später, mit Qdrant + TurboVec)

---

## Nächste Schritte (Konkret)

1. ~~Crawlee eval: abgeschlossen~~ ✅
2. `data/crawler/` anlegen + `kontrapolis_crawl.py` schreiben (~20 Min)
3. Optional: Tag-Seiten-Crawl für netzpolitik.org (z.B. alle Artikel zum Thema "Überwachung")
4. Evaluiert lassen bis konkreter Bedarf

**Das war's mit der Evaluation. Soll ich:**
- **A)** `data/crawler/` jetzt anlegen + kontrapolis-Script schreiben
- **B)** Erstmal so lassen und bei Bedarf wieder herholen
- **C)** Crawlee für eine bestimmte Recherche-Hypothese nutzen (z.B. "Crawle die letzte Woche netzpolitik + heise zum Thema KI-Regulierung")
