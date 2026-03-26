# Cron Status - 2026-03-14

## Aktive Jobs

### Daily Digital Capitalism News Scan
- **Status:** ✅ AKTIV (reaktiviert am 2026-03-14)
- **Schedule:** Täglich 08:00 (Europe/Berlin)
- **Neue Features:**
  - Verwendet jetzt **multi-search-engine** Skill
  - Multiple Suchmaschinen (Google, DuckDuckGo, Brave) mit Fallback
  - Zeitfilter für "past 24 hours" (tbs=qdr:d)
  - Robuster gegen Rate-Limits
- **Zuletzt aktualisiert:** 2026-03-14 12:18 CET

## Frühere Probleme (behoben)
- ❌ Validation Error: Missing 'function' field
- ❌ Rate limits bei DuckDuckGo
- ❌ Keine erfolgreichen Scans seit 2026-03-06

## Lösung
- Installation von **multi-search-engine** Skill (17 Suchmaschinen)
- Fallback-Strategie: Google → DuckDuckGo → Brave
- Direkte LabourNet-Checks bleiben erhalten

## Weitere aktive Jobs
- **Weekly Newsletter Scan:** Sonntags 08:00 (läuft weiterhin)

## Monitoring
- Konsekutive Fehler zurückgesetzt auf 0
- Nächster Lauf: Morgen 08:00
- Bei weiteren Problemen: multi-search-engine bietet Alternativen
