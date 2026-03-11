# Cron Status - 2026-03-10

## Deaktivierte Jobs

### Daily Digital Capitalism News Scan
- **Status:** DEAKTIVIERT (moved to jobs.json.disabled)
- **Grund:** Seit 6 Tagen API-Fehler (22 validation errors, rate limits)
- **Deaktiviert am:** 2026-03-10
- **Durch:** Rook

## Fehler-Details
- Validation Error: Missing 'function' field in tools definition
- Rate limits erreicht täglich
- Keine erfolgreichen Scans seit 2026-03-06

## Reaktivierung
Um den Cron wieder zu aktivieren:
```bash
cd /root/.openclaw/cron
mv jobs.json.disabled jobs.json
```

## Alternative
Der wöchentliche Newsletter-Scan (Sonntags 08:00) läuft weiterhin.
