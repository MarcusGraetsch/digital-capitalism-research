# Weekly Research Digest - Routine

## Ziel
Jeden Sonntag nach dem Newsletter-Scan (08:00) einen kurzen Überblick geben.

## Automatisierung

### Option 1: Manuelle Abfrage (jetzt)
```bash
cd /root/.openclaw/workspace/research
python3 -c "
import sqlite3
conn = sqlite3.connect('articles.db')
cursor = conn.cursor()

# Neue Artikel diese Woche
cursor.execute('''
    SELECT COUNT(*) FROM articles
    WHERE created_at >= datetime('now', '-7 days')
''')
new_count = cursor.fetchone()[0]

# Top Themen
cursor.execute('''
    SELECT category, COUNT(*) FROM articles
    WHERE created_at >= datetime('now', '-7 days')
    AND category IS NOT NULL
    GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5
''')
top_topics = cursor.fetchall()

print(f'📊 Diese Woche: {new_count} neue Artikel')
print('📈 Top Themen:')
for cat, count in top_topics:
    print(f'  - {cat}: {count}')

conn.close()
"
```

### Option 2: Automatisches Telegram (empfohlen)
Erweitere `weekly_pipeline.py` um:
```python
# Am Ende der Pipeline
send_telegram_summary(new_articles_count, top_topics)
```

### Option 3: Dashboard (später)
Interaktive Visualisierung der Weekly Stats.

## Empfohlener Workflow

**Sonntag 08:00:** Newsletter-Scan läuft automatisch
**Sonntag 09:00:** 
- Ich poste Zusammenfassung
- Highlights identifizieren
- Wichtige Artikel markieren für Deep Reading

**Wochenplan:**
- **Mo-Do:** Deep Reading (1-2 Stunden/Tag)
- **Fr:** Review & Planning
- **Sa:** Frei
- **So:** Automatischer Scan + Zusammenfassung

## Metriken tracken

Wöchentlich:
- [ ] Anzahl neue Artikel
- [ ] Neue Kategorien
- [ ] Paywall-Artikel (für später)
- [ ] Highlights für Deep Reading

Monatlich:
- [ ] Gesamtwachstum
- [ ] Ontologie-Erweiterung
- [ ] Citation Metrics Update
